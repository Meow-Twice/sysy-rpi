#!/bin/bash

# Generate ELF from .sy/.c or .S

if ! [ $1 ]; then
    echo "please specify code file." > /dev/stderr
    exit 1
fi

CODE_FILE=$1

NAME="${CODE_FILE%.*}"
SUFFIX="${CODE_FILE##*.}"

if [ $SUFFIX == "S" ]; then
    SOURCE=$CODE_FILE
elif [ $SUFFIX == "c" -o $SUFFIX == "sy" ]; then
    SOURCE="${NAME}.sy.c"
    echo '#include "sylib.h"' > $SOURCE
    cat $CODE_FILE >> $SOURCE
else
    echo "code file must ends with '.sy', '.c' (source) or '.S' (assembly)" > /dev/stderr
    exit 1
fi

GCCPREFIX=
# GCCPREFIX=arm-linux-gnueabihf-

MACHINE_FLAGS="-march=armv7 -mfpu=neon -mfloat-abi=hard"

${GCCPREFIX}gcc ${MACHINE_FLAGS} --static -o $NAME.elf $SOURCE /usr/share/sylib/${GCCPREFIX}sylib.a
