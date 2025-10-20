#ifndef PMP_PREFETCHER_H
#define PMP_PREFETCHER_H

#include "cache.h"
#include <vector>
#include <unordered_map>
#include <cstdint>
#include <iostream>

class PMP {
public:
    PMP(int pattern_len = 64) : pattern_len(pattern_len) {}

    // Call on every memory access
    void access(uint64_t block_number, uint64_t pc);

    // Generate prefetches for a given block
    std::vector<uint64_t> prefetch(uint64_t block_number, uint64_t pc);

private:
    struct PatternEntry {
        std::vector<bool> pattern;
        PatternEntry(int len = 64) : pattern(len, false) {}
    };

    int pattern_len;

    // History table: PC -> pattern entry
    std::unordered_map<uint64_t, PatternEntry> history;

    // Utility to rotate pattern vector
    std::vector<bool> rotate_pattern(const std::vector<bool>& pattern, int offset);
};

#endif
