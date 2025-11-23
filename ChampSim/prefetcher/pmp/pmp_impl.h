#pragma once

#define PMP_IMPL_ADAPTIVE

#ifdef PMP_IMPL_DEFAULT
	#include "pmp.h"
#elif defined(PMP_IMPL_ADAPTIVE)
	#include "pmp_adaptive.h"
#endif
