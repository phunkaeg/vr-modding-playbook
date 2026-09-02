// check.h -- a test harness small enough that nobody has to install anything.
//
// Deliberately not a framework. The appendices' own tests are written as plain
// functions with CHECK(); this keeps them that way.
#pragma once

#include <cstdio>
#include <string>
#include <vector>

namespace vrref_test {

struct Failure { std::string test, expr, file; int line; };

inline std::vector<Failure>& Failures() {
    static std::vector<Failure> f;
    return f;
}

inline const char*& CurrentTest() {
    static const char* t = "<none>";
    return t;
}

inline int& Checks() {
    static int c = 0;
    return c;
}

inline void RecordFailure(const char* expr, const char* file, int line) {
    Failures().push_back({CurrentTest(), expr, file, line});
}

struct TestCase { const char* name; void (*fn)(); };

inline std::vector<TestCase>& Registry() {
    static std::vector<TestCase> r;
    return r;
}

struct Register {
    Register(const char* name, void (*fn)()) { Registry().push_back({name, fn}); }
};

}  // namespace vrref_test

#define CHECK(expr)                                                              \
    do {                                                                         \
        ++::vrref_test::Checks();                                                \
        if (!(expr)) ::vrref_test::RecordFailure(#expr, __FILE__, __LINE__);     \
    } while (0)

#define TEST(name)                                                               \
    static void name();                                                          \
    static ::vrref_test::Register reg_##name(#name, &name);                      \
    static void name()
