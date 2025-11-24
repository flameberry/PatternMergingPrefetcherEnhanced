#pragma once

#define PMP_IMPL_ADAPTIVE_CLIP

#ifdef PMP_IMPL_DEFAULT
	#include "pmp.h"
#elif defined(PMP_IMPL_ADAPTIVE)
	#include "pmp_adaptive.h"
#elif defined(PMP_IMPL_ADAPTIVE_CLIP)
	#include "pmp_adaptive_clip.h"
#endif
