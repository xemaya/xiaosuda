"""Optional durable submission receipt. Other CLI users keep their existing behavior."""
import json
import os
import time
import uuid


def write(path, value):
    if path:
        os.makedirs(os.path.dirname(os.path.abspath(path)),exist_ok=True)
        temp=path+".tmp"
        with open(temp,"w",encoding="utf-8") as f:
            json.dump(value,f,ensure_ascii=False);f.flush();os.fsync(f.fileno())
        os.replace(temp,path)


def submit(call, graph, path, port):
    token=str(uuid.uuid4())
    record={"token":token,"prompt_id":token,"port":port,"phase":"submitting","created":time.time()}
    write(path,record)
    body={"prompt":graph,"client_id":token}
    if path:
        body["prompt_id"]=token
        body["extra_data"]={"director_job":token}
    try:
        result=call("/prompt",body)
    except Exception as exc:
        # A lost response is ambiguous. Recovery searches by this token, never blindly resubmits.
        record["phase"]="rejected" if getattr(exc,"code",None)==400 else "submission_unknown";write(path,record)
        raise
    record.update(phase="submitted",prompt_id=result["prompt_id"])
    write(path,record)
    return result["prompt_id"]


def completed(path, outputs):
    if path:
        with open(path,encoding="utf-8") as f:record=json.load(f)
        record.update(phase="completed",outputs=outputs,finished=time.time())
        write(path,record)
