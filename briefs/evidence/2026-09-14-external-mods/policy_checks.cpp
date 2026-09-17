// Calls the pinned donors' real portable helpers; no engine, graphics API or XR runtime.
#include "mgs5vr/stereo.hpp"
#include "KHARVOX/src/vulkan/VirtualTextureAppend.h"
#include "KHARVOX/src/native/NativeDeferredMemory.h"
#include "titanfall2vr/plugin/src/render/world_rect_gate.h"
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <limits>
#include <vector>

int checks = 0;
void check(bool value, const char* name) {
    ++checks;
    if (!value) { std::fprintf(stderr, "FAIL: %s\n", name); std::exit(1); }
}
int main() {
    using namespace mgs5vr;
    const EyeFov requested{-.94f, .69f, .87f, -.85f};
    const auto envelope = enclosingEyeFov(requested);
    check(bool(envelope), "enclosing optics exist");
    for (const auto size : {std::array<unsigned,2>{1280,720}, {1511,977}}) {
        const auto crop = eyeImageRegion(*envelope, requested, size[0], size[1]);
        check(bool(crop), "crop exists");
        check(crop->fov.left <= requested.left && crop->fov.right >= requested.right
            && crop->fov.up >= requested.up && crop->fov.down <= requested.down,
            "outward-rounded crop contains requested rays");
        for (double u : {0., .13, .5, 1.}) for (double v : {0., .37, 1.}) {
            auto ray = [](EyeFov f, double x, double y) {
                return std::array<double,2>{std::tan(f.left)+(std::tan(f.right)-std::tan(f.left))*x,
                    std::tan(f.up)-(std::tan(f.up)-std::tan(f.down))*y};
            };
            const auto source = ray(*envelope, (crop->x+u*crop->width)/size[0],
                (crop->y+v*crop->height)/size[1]);
            const auto output = ray(crop->fov,u,v);
            check(std::abs(source[0]-output[0]) < 1e-5 && std::abs(source[1]-output[1]) < 1e-5,
                "source and declared subimage rays agree");
        }
    }
    check(!eyeImageRegion(requested,*envelope,1280,720), "missing coverage rejected");
    check(!eyeImageRegion(*envelope,requested,0,720), "zero extent rejected");
    auto invalid = requested; invalid.left = std::numeric_limits<float>::quiet_NaN();
    check(!eyeImageRegion(*envelope,invalid,1280,720), "NaN optics rejected");

    kharvox::VtPageList source{}, destination{};
    source.count=3719; destination.count=4582;
    for (unsigned i=0;i<source.count;++i) source.pages[i]=i+100;
    const auto before=source;
    auto append=kharvox::appendVirtualTexturePages(&destination,&source);
    check(append.valid && append.appended==3610 && append.deferred==109
        && destination.count==8192, "capacity arithmetic at overflow boundary");
    check(std::memcmp(&source,&before,sizeof(source))==0, "source remains byte-identical");
    check(destination.pages[4582]==100 && destination.pages[8191]==3709, "copied range endpoints");
    append=kharvox::appendVirtualTexturePages(&destination,&source);
    check(append.valid && append.appended==0 && append.deferred==3719, "full queue preserves backlog");
    check(!kharvox::appendVirtualTexturePages(&source,&source).valid, "alias rejected");
    check(!kharvox::appendVirtualTexturePages(nullptr,&source).valid, "null rejected");
    source.count=8193;
    check(!kharvox::appendVirtualTexturePages(&destination,&source).valid, "corrupt source count rejected");
    source.count=1; destination.count=8193;
    check(!kharvox::appendVirtualTexturePages(&destination,&source).valid, "corrupt destination count rejected");

    using Queue=kharvox::native::DeferredMemoryFreeQueue<int,2>;
    Queue queue; std::vector<int> released;
    auto release=[&](int request){released.push_back(request);};
    check(queue.begin([]{}), "begin retirement epoch");
    check(!queue.begin([]{}), "overlapping epoch refused");
    check(queue.release(11,true,release)==Queue::Result::Deferred, "defer first resource");
    check(queue.release(11,true,release)==Queue::Result::Refused, "duplicate refused");
    check(queue.release(22,true,release)==Queue::Result::Deferred, "defer second resource");
    check(queue.release(33,true,release)==Queue::Result::Refused, "capacity overflow refused");
    check(released.empty(), "no physical free before explicit completion");
    bool retired=false;
    check(queue.complete(release,[&]{retired=true;})==2 && retired
        && released==std::vector<int>({11,22}), "explicit completion retires in order");
    check(queue.release(44,false,release)==Queue::Result::Released && released.back()==44,
        "outside epoch release is immediate");
    // complete() itself does not check a GPU fence; this is a caller obligation, not a tested GPU guarantee.

    check(!tf2vr::WorldPassViewportPlausible(32,32,5210,3648), "tiny impostor rejected");
    check(tf2vr::WorldPassViewportPlausible(4032,2520,4032,3648), "observed letterbox accepted");
    check(tf2vr::WorldPassViewportPlausible(32,32,0,0), "unknown target is permissive: recorded limitation");
    std::printf("PASS: %d checks; real donor helpers, standalone CPU only; no game/GPU/headset proof.\n",checks);
}
