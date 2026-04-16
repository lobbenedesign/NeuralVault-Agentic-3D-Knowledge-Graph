use simsimd::SpatialSimilarity;

/// Calcola la distanza coseno tra due vettori f32.
/// Se disponibile, usa istruzioni SIMD (AVX, NEON) automaticamente.
pub fn cosine_distance(a: &[f32], b: &[f32]) -> f32 {
    1.0 - f32::cosine(a, b).unwrap_or(0.0) as f32
}

/// Calcola la distanza dot-product tra due vettori f32.
pub fn dot_product(a: &[f32], b: &[f32]) -> f32 {
    f32::dot(a, b).unwrap_or(0.0) as f32
}

/// Calcola la distanza Hamming tra due vettori binari (uint8 packed).
/// Usata per lo Stage 1 della ricerca (ANN binario).
pub fn hamming_distance(a: &[u8], b: &[u8]) -> u32 {
    a.iter()
        .zip(b.iter())
        .map(|(x, y)| (x ^ y).count_ones())
        .sum()
}

/// Calcola la distanza L2 (Euclidea) tra due vettori f32.
pub fn l2_distance(a: &[f32], b: &[f32]) -> f32 {
    (f32::l2sq(a, b).unwrap_or(0.0) as f32).sqrt()
}
