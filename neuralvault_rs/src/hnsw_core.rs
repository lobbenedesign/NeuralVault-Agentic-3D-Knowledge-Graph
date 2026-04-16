use std::collections::{BinaryHeap, HashMap, HashSet};
use std::cmp::Ordering;
use rayon::prelude::*;
use ordered_float::OrderedFloat;

/// Elemento della ricerca (distanza, indice del nodo).
#[derive(Debug, PartialEq, PartialOrd)]
struct SearchResult(OrderedFloat<f32>, usize);

impl Eq for SearchResult {}

impl Ord for SearchResult {
    fn cmp(&self, other: &Self) -> Ordering {
        // Reverse because BinaryHeap is a max-heap, and we want min-dist
        other.0.cmp(&self.0).then_with(|| self.1.cmp(&other.1))
    }
}

pub struct HNSWCore {
    pub dim: usize,
    pub m: usize,
    pub m_max0: usize,
    pub ef_construction: usize,
    
    pub vectors: Vec<f32>,
    pub node_ids: Vec<String>,
    pub id_to_idx: HashMap<String, usize>,
    
    // CSR-like Graph Layout: layers[level] = Flat list of connections
    pub layers_neighbors: Vec<Vec<u32>>,
    pub layers_counts: Vec<Vec<u32>>, // current degrees
    
    pub entry_point: Option<usize>,
    pub max_level: i32,
}

impl HNSWCore {
    pub fn new(dim: usize, m: usize, ef_construction: usize) -> Self {
        Self {
            dim,
            m,
            m_max0: m * 2,
            ef_construction,
            vectors: Vec::new(),
            node_ids: Vec::new(),
            id_to_idx: HashMap::new(),
            layers_neighbors: Vec::new(),
            layers_counts: Vec::new(),
            entry_point: None,
            max_level: -1,
        }
    }

    pub fn get_neighbors(&self, level: usize, node_idx: usize) -> &[u32] {
        let m_max = if level == 0 { self.m_max0 } else { self.m };
        let count = self.layers_counts[level][node_idx] as usize;
        let start = node_idx * m_max;
        &self.layers_neighbors[level][start..start + count]
    }

    pub fn search_layer(
        &self,
        query: &[f32],
        ep_idx: usize,
        ef: usize,
        level: usize,
    ) -> Vec<(usize, f32)> {
        let mut visited = HashSet::new();
        visited.insert(ep_idx);

        let ep_vec = self.get_vector(ep_idx);
        let ep_dist = crate::distance::cosine_distance(query, ep_vec);

        let mut candidates = BinaryHeap::new();
        candidates.push(SearchResult(OrderedFloat(ep_dist), ep_idx));

        let mut dynamic_list: BinaryHeap<(OrderedFloat<f32>, usize)> = BinaryHeap::new();
        dynamic_list.push((OrderedFloat(ep_dist), ep_idx));

        while let Some(SearchResult(c_dist, c_idx)) = candidates.pop() {
            let worst_dist = dynamic_list.peek().map(|(d, _)| *d).unwrap_or(OrderedFloat(f32::MAX));
            if c_dist > worst_dist {
                break;
            }

            let neighbors = self.get_neighbors(level, c_idx);
            for &nb_u32 in neighbors {
                let nb = nb_u32 as usize;
                if visited.insert(nb) {
                    let nb_vec = self.get_vector(nb);
                    let d = crate::distance::cosine_distance(query, nb_vec);
                    
                    let current_worst = dynamic_list.peek().map(|(dw, _)| *dw).unwrap_or(OrderedFloat(f32::MAX));
                    if d < current_worst.0 || dynamic_list.len() < ef {
                        candidates.push(SearchResult(OrderedFloat(d), nb));
                        dynamic_list.push((OrderedFloat(d), nb));
                        if dynamic_list.len() > ef {
                            dynamic_list.pop();
                        }
                    }
                }
            }
        }

        let mut results: Vec<(usize, f32)> = dynamic_list.into_iter()
            .map(|(d, idx)| (idx, d.0))
            .collect();
        results.sort_by(|a, b| a.1.partial_cmp(&b.1).unwrap_or(Ordering::Equal));
        results
    }

    pub fn insert(&mut self, node_id: String, vector: Vec<f32>) {
        let level = self.generate_level();
        let idx = self.node_ids.len();
        
        self.node_ids.push(node_id.clone());
        self.id_to_idx.insert(node_id, idx);
        self.vectors.extend_from_slice(&vector);

        let max_iter = std::cmp::max(level as i32, self.max_level) as usize;
        for l in 0..=max_iter {
            if self.layers_neighbors.len() <= l {
                self.layers_neighbors.push(Vec::new());
                self.layers_counts.push(Vec::new());
            }
            let m_max = if l == 0 { self.m_max0 } else { self.m };
            self.layers_neighbors[l].resize((idx + 1) * m_max, 0);
            self.layers_counts[l].resize(idx + 1, 0);
        }

        if let Some(mut ep) = self.entry_point {
            for l in (level + 1..self.max_level + 1).rev() {
                let results = self.search_layer(&vector, ep, 1, l as usize);
                if let Some(best) = results.first() {
                    ep = best.0;
                }
            }

            for l in (0..std::cmp::min(level, self.max_level) + 1).rev() {
                let neighbors = self.search_layer(&vector, ep, self.ef_construction, l as usize);
                let selected = self.select_neighbors(neighbors, self.m);
                
                for &(nb, _) in &selected {
                    self.add_edge(idx, nb, l as usize);
                    self.add_edge(nb, idx, l as usize);
                }
                if let Some(best) = selected.first() {
                    ep = best.0;
                }
            }
        }

        if level > self.max_level {
            self.entry_point = Some(idx);
            self.max_level = level;
        }
    }

    pub fn delete(&mut self, node_id: String) -> bool {
        if let Some(idx) = self.id_to_idx.remove(&node_id) {
            for l in 0..self.layers_counts.len() {
                let m_max = if l == 0 { self.m_max0 } else { self.m };
                let start = idx * m_max;
                let count = self.layers_counts[l][idx] as usize;
                
                let my_neighbors: Vec<u32> = self.layers_neighbors[l][start..start+count].to_vec();
                for &nb_idx in &my_neighbors {
                    self.remove_edge_from(nb_idx as usize, idx as u32, l);
                }
                self.layers_counts[l][idx] = 0;
            }
            
            if self.entry_point == Some(idx) {
                self.entry_point = None;
            }
            return true;
        }
        false
    }

    fn remove_edge_from(&mut self, u_idx: usize, target: u32, level: usize) {
        let m_max = if level == 0 { self.m_max0 } else { self.m };
        let start = u_idx * m_max;
        let count = self.layers_counts[level][u_idx] as usize;
        
        let mut nbs: Vec<u32> = self.layers_neighbors[level][start..start+count].to_vec();
        if let Some(pos) = nbs.iter().position(|&x| x == target) {
            nbs.remove(pos);
            for (i, &nb) in nbs.iter().enumerate() {
                self.layers_neighbors[level][start + i] = nb;
            }
            self.layers_counts[level][u_idx] -= 1;
        }
    }

    fn add_edge(&mut self, u: usize, v: usize, level: usize) {
        let m_max = if level == 0 { self.m_max0 } else { self.m };
        let count = self.layers_counts[level][u] as usize;
        
        if count < m_max {
            let start = u * m_max;
            self.layers_neighbors[level][start + count] = v as u32;
            self.layers_counts[level][u] += 1;
        } else {
            self.shrink_neighbor_list(u, level, m_max, v);
        }
    }

    fn shrink_neighbor_list(&mut self, u: usize, level: usize, limit: usize, new_nb: usize) {
        let u_vec = self.get_vector(u);
        let m_max = if level == 0 { self.m_max0 } else { self.m };
        let start = u * m_max;
        
        let mut nbs: Vec<u32> = self.layers_neighbors[level][start..start+limit].to_vec();
        nbs.push(new_nb as u32);
        
        let mut with_dists: Vec<(u32, f32)> = nbs.into_iter().map(|nb| {
            (nb, crate::distance::cosine_distance(u_vec, self.get_vector(nb as usize)))
        }).collect();
        
        with_dists.sort_by(|a, b| a.1.partial_cmp(&b.1).unwrap_or(Ordering::Equal));
        
        for (i, (nb, _)) in with_dists.into_iter().take(limit).enumerate() {
            self.layers_neighbors[level][start + i] = nb;
        }
        self.layers_counts[level][u] = limit as u32;
    }

    fn select_neighbors(&self, candidates: Vec<(usize, f32)>, k: usize) -> Vec<(usize, f32)> {
        candidates.into_iter().take(k).collect()
    }

    pub fn __len__(&self) -> usize {
        self.node_ids.len()
    }

    fn generate_level(&self) -> i32 {
        let mut rng = rand::thread_rng();
        let m_l = 1.0 / (self.m as f32).ln();
        let r: f32 = rand::Rng::gen(&mut rng);
        (-r.ln() * m_l).floor() as i32
    }

    pub fn get_edges_sample(&self, max_edges: usize) -> Vec<(String, String)> {
        let mut edges = Vec::new();
        if self.layers_neighbors.is_empty() { return edges; }
        
        // Prendiamo archi dal Layer 0 (quello più denso)
        let l0_nbs = &self.layers_neighbors[0];
        let l0_counts = &self.layers_counts[0];
        let m_max = self.m_max0;
        
        for idx in 0..l0_counts.len() {
            let count = l0_counts[idx] as usize;
            let start = idx * m_max;
            
            for i in 0..count {
                let nb_idx = l0_nbs[start + i] as usize;
                if idx < self.node_ids.len() && nb_idx < self.node_ids.len() {
                    edges.push((self.node_ids[idx].clone(), self.node_ids[nb_idx].clone()));
                }
                if edges.len() >= max_edges {
                    return edges;
                }
            }
        }
        edges
    }

    fn get_vector(&self, idx: usize) -> &[f32] {
        let start = idx * self.dim;
        &self.vectors[start..start + self.dim]
    }
}
