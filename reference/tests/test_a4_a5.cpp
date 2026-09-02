// test_a4_a5.cpp -- the decision logic in A4 and A5 that does not need a target process.
#include <string>
#include <vector>

#include "check.h"
#include "vrref/a4_hook_safety.h"
#include "vrref/a5_capture.h"

using namespace vrref;

// A4.8: verify-then-write. The refusal path is the one that matters, because a mod that
// patches the wrong bytes on a different build is worse than one that does nothing.
TEST(PatchBranchRefusesOnMismatch) {
    // HaloVR's case: verified 74 05 before writing EB 18.
    uint8_t code[]    = {0x74, 0x05, 0x90, 0x90};
    const uint8_t exp[]     = {0x74, 0x05};
    const uint8_t replace[] = {0xEB, 0x18};

    CHECK(PatchBranch(code, exp, replace, 2) == PatchResult::Applied);
    CHECK(code[0] == 0xEB && code[1] == 0x18);

    // A different build: the bytes are not what we expected. Stock behaviour preserved,
    // and -- the part to assert -- the target is left BYTE-IDENTICAL.
    uint8_t other[] = {0x75, 0x05, 0x90, 0x90};
    const uint8_t before[4] = {0x75, 0x05, 0x90, 0x90};
    CHECK(PatchBranch(other, exp, replace, 2) == PatchResult::RefusedBytesDiffer);
    for (int i = 0; i < 4; ++i) CHECK(other[i] == before[i]);
}

// A refused unprotect must also leave the bytes alone -- the failure path people forget.
TEST(PatchBranchLeavesBytesOnProtectFailure) {
    uint8_t code[] = {0x74, 0x05};
    const uint8_t exp[]     = {0x74, 0x05};
    const uint8_t replace[] = {0xEB, 0x18};
    auto failProtect = [](void*, size_t, bool) { return false; };
    CHECK(PatchBranch(code, exp, replace, 2, failProtect) == PatchResult::ProtectFailed);
    CHECK(code[0] == 0x74 && code[1] == 0x05);
}

// A4.4: the re-entrancy guard nests, so a hook calling a hooked API does not recurse.
TEST(InternalScopeNests) {
    CHECK(!IsReentrant());
    {
        InternalScope a;
        CHECK(IsReentrant());
        {
            InternalScope b;
            CHECK(IsReentrant());
        }
        CHECK(IsReentrant());     // still inside `a`
    }
    CHECK(!IsReentrant());
}

// A4.5: an all-zero census is not evidence of survival. This is the predicate that
// stops "the guard works" and "the trigger never fired" producing identical logs.
TEST(CensusDistinguishesSurvivalFromSilence) {
    TriggerCensus t;
    CHECK(!CensusExercised(t));                 // nothing happened: prove nothing
    t.focusEvents.fetch_add(1);
    CHECK(CensusExercised(t));
}

// A4.9: anchors are module-relative. The same RVA against two bases must resolve
// differently -- which is the whole reason a hard-coded absolute address rots.
TEST(AnchorResolvesAgainstLiveBase) {
    Anchor a{"Dunia.dll", 0x1234, 0x7FF600000000ull};
    CHECK(a.Resolve() == 0x7FF600001234ull);
    a.liveBase = 0x180000000ull;                // ASLR moved it
    CHECK(a.Resolve() == 0x180001234ull);
}

// A5: the burst capture is armed, bounded and self-terminating. The failure it exists
// to prevent is "it captured forever and changed the timing I was measuring".
TEST(BurstCaptureIsArmedAndBounded) {
    std::vector<std::string> written;
    auto cap = MakeBurstCapture([&written](const char* n) { written.push_back(n); });

    Pose pose{};
    pose.position = {0, 1.7f, 0};

    // Not armed: nothing is written, however many frames go by.
    for (uint64_t f = 0; f < 100; ++f)
        cap.OnFrame((f & 1) ? EyeIndex::Right : EyeIndex::Left, f, pose);
    CHECK(written.empty());

    // Armed once: exactly kFrames captured, then it stops on its own.
    cap.Arm();
    for (uint64_t f = 0; f < 100; ++f)
        cap.OnFrame((f & 1) ? EyeIndex::Right : EyeIndex::Left, f, pose);
    CHECK(written.size() == static_cast<size_t>(decltype(cap)::kFrames));
    CHECK(!cap.Capturing());

    // Arming again starts a NEW burst id, so two bursts never interleave in a listing.
    const int firstBurst = cap.BurstId();
    cap.Arm();
    cap.OnFrame(EyeIndex::Left, 200, pose);
    CHECK(cap.BurstId() == firstBurst + 1);
}

// A5's actual claim: everything you cannot reconstruct later goes in the FILENAME,
// so the directory listing IS the analysis. Assert the name carries all four facts.
TEST(BurstFilenameCarriesTheEvidence) {
    std::vector<std::string> written;
    auto cap = MakeBurstCapture([&written](const char* n) { written.push_back(n); });
    Pose pose{};
    pose.position = {0, 1.7f, 0};

    cap.Arm();
    cap.OnFrame(EyeIndex::Right, 4242, pose);

    CHECK(written.size() == 1);
    const std::string& n = written[0];
    CHECK(n.find("eyeR")   != std::string::npos);   // which eye we BELIEVED it was
    CHECK(n.find("seq00")  != std::string::npos);   // order within the burst
    CHECK(n.find("4242")   != std::string::npos);   // the engine's own frame index
    CHECK(n.find("+1.7000") != std::string::npos);  // the pose it was rendered at
}
