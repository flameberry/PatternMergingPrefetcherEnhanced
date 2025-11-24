#ifndef IPCP_L1_H
#define IPCP_L1_H

#include "cache.h"

namespace ipcp_l1 {

#define DO_PREF
// #define SIG_DEBUG_PRINT				    // Uncomment to turn on Debug Print
#ifdef SIG_DEBUG_PRINT
#define SIG_DP(x) x
#else
#define SIG_DP(x)
#endif

constexpr int S_TYPE = 1;    // stream
constexpr int CS_TYPE = 2;   // constant stride
constexpr int CPLX_TYPE = 3; // complex stride
constexpr int NL_TYPE = 4;   // next line

constexpr int NUM_BLOOM_ENTRIES = 4096; // For book-keeping purposes
constexpr int NUM_IP_TABLE_L1_ENTRIES = 64;
constexpr int NUM_CSPT_ENTRIES = 128; // = 2^NUM_SIG_BITS
constexpr int NUM_SIG_BITS = 7;       // num of bits in signature
constexpr int NUM_IP_INDEX_BITS = 6;
constexpr int NUM_IP_TAG_BITS = 9;
constexpr int NUM_PAGE_TAG_BITS = 2;
constexpr int CPLX_DIST = 0;
constexpr int NUM_OF_RR_ENTRIES = 32;      // recent request filter entries
constexpr int RR_TAG_MASK = 0xFFF;         // 12 bits of prefetch line address are stored in recent request filter
constexpr int NUM_RST_ENTRIES = 8;         // region stream table entries
constexpr int MAX_POS_NEG_COUNT = 64;      // 6-bit saturating counter
constexpr int NUM_OF_LINES_IN_REGION = 32; // 32 cache lines in 2KB region
constexpr int REGION_OFFSET_MASK = 0x1F;   // 5-bit offset for 2KB region

class IP_TABLE_L1 {
public:
    uint64_t ip_tag;
    uint64_t last_vpage;       // last page seen by IP
    uint64_t last_line_offset; // last cl offset in the 4KB page
    int64_t last_stride;       // last stride observed
    uint16_t ip_valid;         // valid bit
    int conf;                  // CS confidence
    uint16_t signature;        // CPLX signature
    uint16_t str_dir;          // stream direction
    uint16_t str_valid;        // stream valid
    uint16_t pref_type;        // pref type or class for book-keeping purposes.

    IP_TABLE_L1() {
        ip_tag = 0;
        last_vpage = 0;
        last_line_offset = 0;
        last_stride = 0;
        ip_valid = 0;
        signature = 0;
        conf = 0;
        str_dir = 0;
        str_valid = 0;
        pref_type = 0;
    };
};

class CONST_STRIDE_PRED_TABLE {
public:
    int stride;
    int conf;

    CONST_STRIDE_PRED_TABLE() {
        stride = 0;
        conf = 0;
    };
};

/* This class is for bookkeeping purposes only. */
class STAT_COLLECT {
public:
    uint64_t useful;
    uint64_t filled;
    uint64_t misses;
    uint64_t polluted_misses;

    uint8_t bl_filled[NUM_BLOOM_ENTRIES];
    uint8_t bl_request[NUM_BLOOM_ENTRIES];

    STAT_COLLECT() {
        useful = 0;
        filled = 0;
        misses = 0;
        polluted_misses = 0;

        for (int i = 0; i < NUM_BLOOM_ENTRIES; i++) {
            bl_filled[i] = 0;
            bl_request[i] = 0;
        }
    };
};

class REGION_STREAM_TABLE {
public:
    uint64_t region_id;
    uint64_t tentative_dense;                    // tentative dense bit
    uint64_t trained_dense;                      // trained dense bit
    uint64_t pos_neg_count;                      // positive/negative stream counter
    uint64_t dir;                                // direction of stream - 1 for +ve and 0 for -ve
    uint64_t lru;                                // lru for replacement
    uint8_t line_access[NUM_OF_LINES_IN_REGION]; // bit vector to store which lines in the 2KB region have been accessed
    REGION_STREAM_TABLE() {
        region_id = 0;
        tentative_dense = 0;
        trained_dense = 0;
        pos_neg_count = MAX_POS_NEG_COUNT / 2;
        dir = 0;
        lru = 0;
        for (int i = 0; i < NUM_OF_LINES_IN_REGION; i++)
            line_access[i] = 0;
    };
};

uint16_t update_sig_l1(uint16_t old_sig, int delta);
int update_conf(int stride, int pred_stride, int conf);
uint64_t hash_bloom(uint64_t addr);
uint64_t hash_page(uint64_t addr);
void stat_col_L1(uint64_t addr, uint8_t cache_hit, uint8_t cpu, uint64_t ip);
/* encode_metadata: The stride, prefetch class type and speculative nl fields are encoded in the metadata. */
uint32_t encode_metadata(int stride, uint16_t type, int spec_nl);
} // namespace ipcp_l1

#endif