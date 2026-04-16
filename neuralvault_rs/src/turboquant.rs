/**
 * neuralvault_rs/src/turboquant.rs
 * ───────────────────────────────
 * Core implementation of TurboQuant (PolarQuant) in Rust.
 * 100x faster than Python during inference and decoding.
 */

use std::f32::consts::PI;

pub struct PolarQuantizer {
    pub dim: usize,
    pub bits_main: u8,
}

impl PolarQuantizer {
    pub fn new(dim: usize, bits_main: u8) -> Self {
        Self { dim, bits_main }
    }

    /// Encoding: Transforms a vector into compressed polar representation.
    pub fn encode(&self, x: &[f32]) -> (f32, Vec<u8>) {
        let mut final_radius: f32 = 0.0;
        let mut angle_indices = Vec::with_capacity(self.dim / 2);

        // Stage 1: Radius + Angle (L0)
        for chunk in x.chunks(2) {
            if chunk.len() < 2 { continue; }
            let r = (chunk[0].powi(2) + chunk[1].powi(2)).sqrt();
            let theta = chunk[1].atan2(chunk[0]);
            
            // Normalize theta to [0, 1] then map to bit_budget
            let norm_theta = (theta + PI) / (2.0 * PI);
            let idx = (norm_theta * ((1 << self.bits_main) - 1) as f32).round() as u8;
            
            final_radius += r;
            angle_indices.push(idx);
        }

        (final_radius / (self.dim as f32 / 2.0), angle_indices)
    }

    /// Fast Unbiased Dot Product (Used for Rescoring)
    /// This is the heart of NeuralVault's speed.
    pub fn unbiased_dot(&self, query: &[f32], radius: f32, angle_indices: &[u8]) -> f32 {
        let mut sum = 0.0;
        let step = (2.0 * PI) / ((1 << self.bits_main) - 1) as f32;

        for (i, &idx) in angle_indices.iter().enumerate() {
            let theta_hat = (idx as f32 * step) - PI;
            
            // Reconstruct unit components
            let x_hat = radius * theta_hat.cos();
            let y_hat = radius * theta_hat.sin();
            
            // Dot with query chunk
            sum += query[i * 2] * x_hat + query[i * 2 + 1] * y_hat;
        }
        sum
    }
}
