#include <cstdio>

#include "check.h"

int main() {
    using namespace vrref_test;

    int failedTests = 0;
    for (const TestCase& t : Registry()) {
        CurrentTest() = t.name;
        const size_t before = Failures().size();
        t.fn();
        const size_t added = Failures().size() - before;
        if (added) {
            ++failedTests;
            std::printf("FAIL  %-46s %zu check(s)\n", t.name, added);
        } else {
            std::printf("pass  %s\n", t.name);
        }
    }

    std::printf("\n%zu tests, %d checks", Registry().size(), Checks());
    if (failedTests == 0) {
        std::printf(" - all passed\n");
        return 0;
    }

    std::printf(" - %d TEST(S) FAILED\n\n", failedTests);
    for (const Failure& f : Failures())
        std::printf("  %s\n    %s:%d\n    CHECK(%s)\n", f.test.c_str(), f.file.c_str(), f.line, f.expr.c_str());
    return 1;
}
