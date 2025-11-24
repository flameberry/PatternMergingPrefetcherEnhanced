#include "pmp_impl.h"

#ifdef PMP_IMPL_DEFAULT
	#include "pmp.inc"
#elif defined(PMP_IMPL_ADAPTIVE)
	#include "pmp_adaptive.inc"
#elif defined(PMP_IMPL_ADAPTIVE_CLIP)
	#include "pmp_adaptive_clip.inc"
#endif
