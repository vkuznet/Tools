#!/usr/bin/env bash
#
# Author: Valentin Kuznetsov <vkuznet@gmail.com>
# Description: shell script to create simple C++ project
#              includes project area (header/source), main.cpp and Makefile
# Usage: make_cpp_project.sh <project_name>

# check number of input arguments
EXPECTED_ARGS=1
E_BADARGS=65
if [ $# -ne $EXPECTED_ARGS ]
then
    echo "Usage: `basename $0` project_name"
    exit $E_BADARGS
fi
project=$1
if [ -d $project ]; then
    echo "$project directory already exists"
    exit 1
fi
mkdir -p $project/$project
cd $project

# capitalize
Project=`echo $project | awk '{z=split($1,a,""); print toupper(a[1])substr($1,2,z)}'`
PROJECT=`echo $project | tr '[a-z]' '[A-Z]'`

echo "Create Makefile"
cat > Makefile << EOF
include Makefile.mk

CPPFLAGS=\$(CPPUNIT_INCLUDES) -I\$(SRC_DIR)/$project
all: prepare lib$Project.so Demo

Demo: lib$Project.so main.o
	\$(LINKER) main.o \$(LDFLAGS) -L\$(SRC_DIR)/lib -l$Project -o \$@

fc_objects := \$(patsubst %.cpp,%.o,\$(wildcard $project/*.cpp))

lib$Project.so: \$(fc_objects)
	\$(LINKER) \$+ -shared -o \$(SRC_DIR)/lib/\$@

prepare:
	mkdir -p \$(SRC_DIR)/lib

clean:
	rm -f *.o */*.o *.so
	rm -f Demo
	rm -f \$(fc_objects)
EOF

echo "Create Makefile.mk"
cat > Makefile.mk << EOF.mk
# Local setup, change as desired
SRC_DIR:=\$(PWD)

CXXOTHERFLAGS :=
UNAME:=\$(shell uname -s)
ifeq (\$(UNAME), Linux)
CXXOTHERFLAGS := -D__USE_XOPEN2K8
endif

# Compiler stuff
CPPFLAGS=-I\$(SRC_DIR)
# CXXFLAGS=-O3 -g -std=c++0x -fPIC -pthread \$(CXXOTHERFLAGS)
# LDFLAGS= -std=c++0x -pthread
CXXFLAGS=-O3 -g -fPIC -pthread \$(CXXOTHERFLAGS)
LDFLAGS= -pthread
CXX:=g++
LINKER:=g++

# CPP unit stuff
CPPUNIT_INCLUDES := -I/opt/local/include
CPPUNIT_LIB_PATH := -L/opt/local/lib
CPPUNIT_LIB := \$(CPPUNIT_LIB_PATH) -lcppunit

# sigc++ stuff
SIGC_INCLUDES := -I/opt/local/include/sigc++-2.0 -I/opt/local/lib/sigc++-2.0/include
SIGC_LIB_PATH := -L/opt/local/lib
SIGC_LIB := \$(SIGC_LIB_PATH) -lsigc-2.0.0

# Boost stuff
BOOST_INC=/opt/local/include/boost
BOOST_INCLUDES := -I\$(BOOST_INC)
EOF.mk

echo "Create main.cpp"
cat > main.cpp << EOF.main
#include "$project.h"
#include <iostream>

int main(int argc, const char *argv[])
{
    std::cout << "Hello $project" << std::endl;
    return 0;
}
EOF.main

echo "Create $project.h"
cat > $project/$project.h << EOF.pr
#ifndef ${PROJECT}_H
#define ${PROJECT}_H

class $Project
{
    public:
        void method();
};

#endif /* end of include guard: ${PROJECT}_H */
EOF.pr

echo "Create $project.cpp"
cat > $project/$project.cpp << EOF.cpp
#include "$project.h"
#include <iostream>
void $Project::method() {
    std::cout << "$Project::method" << std::endl;
};
EOF.cpp

echo "Compile $project"
make

