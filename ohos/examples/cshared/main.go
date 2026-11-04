package main

/*
#include <stdlib.h>
*/
import "C"

import (
	"fmt"
	"runtime"
	"unsafe"
)

//export OhosHello
func OhosHello() *C.char {
	runtime.GC()
	return C.CString(fmt.Sprintf("%s/%s %s openharmony=%t", runtime.GOOS, runtime.GOARCH, runtime.Version(), runtime.IsOpenharmony))
}

//export OhosFree
func OhosFree(value *C.char) { C.free(unsafe.Pointer(value)) }

func main() {}
