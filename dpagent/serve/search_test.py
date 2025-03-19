from langserve import RemoteRunnable

chain = RemoteRunnable("http://localhost:8000/search_code/")
res = chain.invoke(
    {
        "proj_path": "/home/jlhuang/turbox-hjl/sourcecode/turbox-c6490p-lu1.0-dev.release.FC.r001002/apps_proc/src/kernel/msm-5.4/techpack/camera",
        "language": "c++",
        "query": "How to initilize camera sensor?",
    }
)
print(res)
