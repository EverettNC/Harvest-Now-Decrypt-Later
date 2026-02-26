use pyo3::prelude::*;

/// This is our first Rust function that Python will be able to call!
#[pyfunction]
fn rust_engine_status() -> PyResult<String> {
    Ok("The Christman AI Project: Constant-time Rust backend is ONLINE.".to_string())
}

/// A Python module implemented in Rust.
#[pymodule]
fn christman_pq_rust(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(rust_engine_status, m)?)?;
    Ok(())
}
// Hardening the Silicon: Constant-Time Comparison
pub fn constant_time_eq(a: &[u8], b: &[u8]) -> bool {
    if a.len() != b.len() {
        return false;
    }
    let mut res = 0;
    for (x, y) in a.iter().zip(b.iter()) {
        res |= x ^ y; // XOR every byte—if they are the same, res stays 0
    }
    res == 0 // Only true if every single XOR was a match
}
