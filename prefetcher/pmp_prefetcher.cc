#include "pmp_prefetcher.h"

void PMP::access(uint64_t block_number, uint64_t pc) {
    // Initialize history for new PC
    if (history.find(pc) == history.end()) {
        history[pc] = PatternEntry(pattern_len);
    }

    // Mark current block as accessed
    int offset = block_number % pattern_len;
    history[pc].pattern[offset] = true;
}

std::vector<bool> PMP::rotate_pattern(const std::vector<bool>& pattern, int offset) {
    std::vector<bool> rotated(pattern.size(), false);
    for (size_t i = 0; i < pattern.size(); ++i) {
        rotated[i] = pattern[(i + offset) % pattern.size()];
    }
    return rotated;
}

std::vector<uint64_t> PMP::prefetch(uint64_t block_number, uint64_t pc) {
    std::vector<uint64_t> prefetch_blocks;

    auto it = history.find(pc);
    if (it == history.end()) return prefetch_blocks;

    int region_offset = block_number % pattern_len;
    auto pattern = it->second.pattern;

    // Prefetch forward/backward based on pattern
    for (int d = 1; d < pattern_len; ++d) {
        for (int dir = -1; dir <= 1; dir += 2) {
            int pf_offset = region_offset + dir * d;
            if (pf_offset < 0 || pf_offset >= pattern_len) continue;
            if (pattern[pf_offset]) {
                uint64_t pf_block = block_number + dir * d;
                if (pf_block != block_number) {
                    prefetch_blocks.push_back(pf_block);
                }
            }
        }
    }

    // Clear current block in pattern to avoid repeated prefetch
    it->second.pattern[region_offset] = false;
    return prefetch_blocks;
}
