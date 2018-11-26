#!/usr/bin/env python3

from kninja import *
import sys
import os.path

# Project Definition
# ==================

proj = KProject()

# Compile the definition
#
imported_k_files = [ proj.source('kore.md').then(proj.tangle().output(proj.tangleddir('kore.k'))) ]
tangled = proj.source('matching-logic-prover.md') \
              .then(proj.tangle().output(proj.tangleddir('matching-logic-prover.k')))


java = tangled.then(proj.kompile('java')
                        .variables(directory = proj.builddir('prover-java'))
                        .implicit(imported_k_files)
                   ).alias('prover-java')
llvm = tangled.then(proj.kompile(backend = 'llvm')
                        .variables(directory = proj.builddir('prover-llvm'))
                        .implicit(imported_k_files + ['llvm-backend'])
                   ).alias('prover-llvm')

# Unit tests
#
proj.source('unit-tests.md') \
    .then(proj.tangle().output(proj.tangleddir('unit-tests-spec.k'))) \
    .then(java.kprove()) \
    .then(proj.check(proj.source('t/unit-tests.expected'))) \
    .alias('unit-tests') \
    .default()

# Helper function for running tests
#
def do_test(defn, file, expected):
    proj.source(file) \
        .then(defn.krun()) \
        .then(proj.check(proj.source(expected))
                     .variables(flags = '--ignore-all-space')) \
        .alias(file + '.test') \
        .default()

do_test(java, 't/foo', 't/foo.expected')
do_test(llvm, 't/foo', 't/foo.expected')


# Build the LLVM Backend
# ======================

# TODO: This code should be migrated to KNinja

llvm_rule = proj.rule( 'build-llvm-backend'
                     , description = 'Building the LLVM backend'
                     , command = 'lib/setup-llvm "$build_dir" "$llvm_backend_repo"'
                     ).output('llvm-backend')
nullTarget = Target(proj, '')
nullTarget.then(llvm_rule
                    .variables( build_dir = proj.builddir('llvm-backend')
                              , llvm_backend_repo = proj.extdir('llvm-backend')
                              ) \
                    .pool('console')
               )
