#define XP_EXPORT
#include "abi.h"
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <d3d12.h>
#include <dxgi1_4.h>
#include <wrl/client.h>
#include <cstdio>
#include <stdexcept>
using Microsoft::WRL::ComPtr;
namespace {
void check(HRESULT hr) { if (FAILED(hr)) throw std::runtime_error("D3D12 operation failed"); }
LRESULT CALLBACK proc(HWND h,UINT m,WPARAM w,LPARAM l) {
    if (m==WM_CLOSE) { ShowWindow(h,SW_HIDE); return 0; }
    return DefWindowProcW(h,m,w,l);
}
struct Window {
    HWND h=nullptr;
    HANDLE event=nullptr;
    ~Window() { if(event) CloseHandle(event); if(h) DestroyWindow(h); }
};
}
int XPClearDemo(uint32_t frames) {
    if (!frames || frames>36000) return -1;
    // Demonstrates host D3D12 only: not an Xbox command-stream or shader translator.
    try {
        auto instance=GetModuleHandleW(nullptr);
        WNDCLASSW wc{}; wc.lpfnWndProc=proc; wc.hInstance=instance; wc.lpszClassName=L"XboxPCResearch";
        if (!RegisterClassW(&wc) && GetLastError()!=ERROR_CLASS_ALREADY_EXISTS) return -1;
        Window win;
        win.h=CreateWindowExW(0,wc.lpszClassName,L"XboxPC — D3D12 host test (not an Xbox game)",
            WS_OVERLAPPED|WS_CAPTION|WS_SYSMENU|WS_VISIBLE,CW_USEDEFAULT,CW_USEDEFAULT,800,480,
            nullptr,nullptr,instance,nullptr);
        if(!win.h) return -1;
        ComPtr<IDXGIFactory4> factory; check(CreateDXGIFactory1(IID_PPV_ARGS(&factory)));
        ComPtr<ID3D12Device> device;
        // Hardware only. No automatic WARP fallback concealing lack of GPU support.
        check(D3D12CreateDevice(nullptr,D3D_FEATURE_LEVEL_11_0,IID_PPV_ARGS(&device)));
        D3D12_COMMAND_QUEUE_DESC qd{}; qd.Type=D3D12_COMMAND_LIST_TYPE_DIRECT;
        ComPtr<ID3D12CommandQueue> queue; check(device->CreateCommandQueue(&qd,IID_PPV_ARGS(&queue)));
        DXGI_SWAP_CHAIN_DESC1 sd{}; sd.Width=800; sd.Height=480; sd.Format=DXGI_FORMAT_R8G8B8A8_UNORM;
        sd.SampleDesc.Count=1; sd.BufferUsage=DXGI_USAGE_RENDER_TARGET_OUTPUT; sd.BufferCount=2;
        sd.SwapEffect=DXGI_SWAP_EFFECT_FLIP_DISCARD;
        ComPtr<IDXGISwapChain1> initial;
        check(factory->CreateSwapChainForHwnd(queue.Get(),win.h,&sd,nullptr,nullptr,&initial));
        ComPtr<IDXGISwapChain3> swap; check(initial.As(&swap));
        check(factory->MakeWindowAssociation(win.h,DXGI_MWA_NO_ALT_ENTER));
        D3D12_DESCRIPTOR_HEAP_DESC hd{}; hd.Type=D3D12_DESCRIPTOR_HEAP_TYPE_RTV; hd.NumDescriptors=2;
        ComPtr<ID3D12DescriptorHeap> heap; check(device->CreateDescriptorHeap(&hd,IID_PPV_ARGS(&heap)));
        ComPtr<ID3D12Resource> targets[2];
        auto stride=device->GetDescriptorHandleIncrementSize(D3D12_DESCRIPTOR_HEAP_TYPE_RTV);
        auto handle=heap->GetCPUDescriptorHandleForHeapStart();
        for(UINT i=0;i<2;++i) {
            check(swap->GetBuffer(i,IID_PPV_ARGS(&targets[i])));
            device->CreateRenderTargetView(targets[i].Get(),nullptr,handle); handle.ptr+=stride;
        }
        ComPtr<ID3D12CommandAllocator> allocator;
        check(device->CreateCommandAllocator(D3D12_COMMAND_LIST_TYPE_DIRECT,IID_PPV_ARGS(&allocator)));
        ComPtr<ID3D12GraphicsCommandList> list;
        check(device->CreateCommandList(0,D3D12_COMMAND_LIST_TYPE_DIRECT,allocator.Get(),nullptr,IID_PPV_ARGS(&list)));
        check(list->Close());
        ComPtr<ID3D12Fence> fence; check(device->CreateFence(0,D3D12_FENCE_FLAG_NONE,IID_PPV_ARGS(&fence)));
        win.event=CreateEventW(nullptr,FALSE,FALSE,nullptr); if(!win.event) return -1;
        for(uint32_t frame=0;frame<frames && IsWindowVisible(win.h);++frame) {
            MSG msg{}; while(PeekMessageW(&msg,win.h,0,0,PM_REMOVE)) { TranslateMessage(&msg); DispatchMessageW(&msg); }
            if(!IsWindowVisible(win.h)) break;
            check(allocator->Reset()); check(list->Reset(allocator.Get(),nullptr));
            auto index=swap->GetCurrentBackBufferIndex();
            D3D12_RESOURCE_BARRIER barrier{}; barrier.Type=D3D12_RESOURCE_BARRIER_TYPE_TRANSITION;
            barrier.Transition.pResource=targets[index].Get();
            barrier.Transition.Subresource=D3D12_RESOURCE_BARRIER_ALL_SUBRESOURCES;
            barrier.Transition.StateBefore=D3D12_RESOURCE_STATE_PRESENT;
            barrier.Transition.StateAfter=D3D12_RESOURCE_STATE_RENDER_TARGET;
            list->ResourceBarrier(1,&barrier);
            auto rtv=heap->GetCPUDescriptorHandleForHeapStart(); rtv.ptr+=index*stride;
            uint32_t buttons=0; XPGetButtons(0,&buttons);
            float color[4]={buttons ? .3f : .02f,.15f+float(frame%120)/240.f,.08f,1.f};
            list->ClearRenderTargetView(rtv,color,0,nullptr);
            barrier.Transition.StateBefore=D3D12_RESOURCE_STATE_RENDER_TARGET;
            barrier.Transition.StateAfter=D3D12_RESOURCE_STATE_PRESENT;
            list->ResourceBarrier(1,&barrier); check(list->Close());
            ID3D12CommandList* lists[]={list.Get()}; queue->ExecuteCommandLists(1,lists);
            // Wait before reusing allocator/resources. Deliberately simple, not a performance claim.
            check(queue->Signal(fence.Get(),static_cast<UINT64>(frame)+1));
            check(fence->SetEventOnCompletion(static_cast<UINT64>(frame)+1,win.event));
            if(WaitForSingleObject(win.event,10000)!=WAIT_OBJECT_0) throw std::runtime_error("GPU fence timed out");
            check(swap->Present(1,0));
        }
        return 0;
    } catch(const std::exception& e) { std::fprintf(stderr,"XboxPC graphics: %s\n",e.what()); return -1; }
}
