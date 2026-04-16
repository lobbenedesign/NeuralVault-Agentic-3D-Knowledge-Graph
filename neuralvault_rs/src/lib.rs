use pyo3::prelude::*;

mod distance;
mod hnsw_core;
pub mod turboquant;

#[pyclass]
pub struct PyHNSW {
    inner: hnsw_core::HNSWCore,
}

#[pymethods]
impl PyHNSW {
    #[new]
    pub fn new(dim: usize, m: usize, ef_construction: usize) -> Self {
        PyHNSW {
            inner: hnsw_core::HNSWCore::new(dim, m, ef_construction),
        }
    }

    /// Elimina un nodo dal grafo.
    pub fn delete(&mut self, node_id: String) -> bool {
        self.inner.delete(node_id)
    }

    /// Ritorna il numero di nodi indicizzati.
    pub fn __len__(&self) -> usize {
        self.inner.node_ids.len()
    }

    /// Inserisce un vettore nel grafo.
    pub fn insert(&mut self, node_id: String, vector: Vec<f32>) {
        self.inner.insert(node_id, vector);
    }

    /// Ricerca i top-k vicini.
    pub fn search(
        &self,
        query: Vec<f32>,
        k: usize,
        ef: usize,
    ) -> Vec<(String, f32)> {
        // Fase 1: Scendi dai layer alti all'entry_point del layer 0
        let mut ep = if let Some(e) = self.inner.entry_point { e } else { return Vec::new() };
        
        for l in (1..=(self.inner.max_level as usize)).rev() {
            let results = self.inner.search_layer(&query, ep, 1, l);
            if let Some(best) = results.first() {
                ep = best.0;
            }
        }

        // Fase 2: Ricerca precisa al layer 0
        let results = self.inner.search_layer(&query, ep, ef, 0);
        
        results.into_iter()
            .take(k)
            .map(|(idx, dist)| {
                (self.inner.node_ids[idx].clone(), dist)
            })
            .collect()
    }

    /// Estrae un campione di archi per visualizzazione.
    pub fn get_edges_sample(&self, max_edges: usize) -> Vec<(String, String)> {
        self.inner.get_edges_sample(max_edges)
    }

    /// Ritorna il numero totale di archi nel grafo.
    pub fn total_edges(&self) -> usize {
        self.inner.layers_counts.iter().map(|c| c.iter().sum::<u32>() as usize).sum()
    }

    /// Ritorna il livello massimo attuale.
    pub fn max_level(&self) -> i32 {
        self.inner.max_level
    }

    /// Blocca l'indice nella memoria fisica (Hardware Pinning).
    /// Ottimizzato per NVIDIA Grace (Unified Memory) e Apple Silicon.
    pub fn pin_to_hardware(&self) -> bool {
        #[cfg(unix)]
        unsafe {
            let ptr = self.inner.vectors.as_ptr() as *const libc::c_void;
            let size = self.inner.vectors.len() * std::mem::size_of::<Vec<f32>>();
            if libc::mlock(ptr, size) == 0 {
                println!("🏎️ [Hardware] HNSW Index pinned to Fast RAM/HBM.");
                return true;
            }
        }
        false
    }

    /// Ritorna la dimensione dei vettori.
    pub fn dim(&self) -> usize {
        self.inner.dim
    }
}

#[pyclass]
pub struct RustTurboQuant {
    inner: turboquant::PolarQuantizer,
}

#[pymethods]
impl RustTurboQuant {
    #[new]
    pub fn new(dim: usize, bits_main: u8) -> Self {
        RustTurboQuant {
            inner: turboquant::PolarQuantizer::new(dim, bits_main),
        }
    }

    pub fn encode(&self, x: Vec<f32>) -> (f32, Vec<u8>) {
        self.inner.encode(&x)
    }

    pub fn unbiased_dot(&self, query: Vec<f32>, radius: f32, angle_indices: Vec<u8>) -> f32 {
        self.inner.unbiased_dot(&query, radius, &angle_indices)
    }
}

/// Il modulo Rust che verrà importato in Python.
#[pymodule]
fn neuralvault_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyHNSW>()?;
    m.add_class::<RustTurboQuant>()?;
    Ok(())
}
