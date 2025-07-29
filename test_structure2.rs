pub mod magic_header {
    pub const MAGIC_BYTES: [u8; 4] = [0x47, 0x4C, 0x49, 0x44];
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test1() {}

    #[cfg(feature = "compression")]
    mod command_compression_tests {
        #[test]
        fn test() {}
    }

    #[cfg(feature = "compression")]
    mod zstd_backend_tests {
        #[test]
        fn test() {}
    }

    mod response_decompression_tests {
        #[test]
        fn test() {}
    }
}
