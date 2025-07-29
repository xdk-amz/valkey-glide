#[cfg(test)]
mod tests {
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
}
