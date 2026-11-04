import sys
import json
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:5000"

def request_json(url, method="GET", data=None):
    headers = {"Content-Type": "application/json"}
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            res_body = resp.read().decode("utf-8")
            return resp.status, json.loads(res_body) if res_body else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(err_body)
        except Exception:
            return e.code, {"error": err_body}
    except Exception as e:
        print(f"[X] Khong the ket noi den Backend ({BASE_URL}). Dam bao 'python run.py' dang chay!")
        sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print("Huong dan dung: python smoke_play.py <ACCESS_CODE>")
        sys.exit(1)

    code = sys.argv[1].strip()
    print(f"=== KHONG KHAI SMOKE TEST LUONG LAM BAI (MA DE: {code}) ===")

    # 1. Tra cuu de thi qua GET /api/play/lookup
    print("\n[1] Tra cuu bo de thi qua GET /api/play/lookup...")
    status, res = request_json(f"{BASE_URL}/api/play/lookup?code={code}")
    if status != 200:
        status, res = request_json(f"{BASE_URL}/api/play/lookup?access_code={code}")
    
    print(f"--> Status: {status} | Response: {res}")
    if status != 200:
        print(f"[X] Tra cuu de thi that bai (Status {status})!")
        return

    print("[V] TRA CUU DE THI THANH CONG!")

    # 2. Tham gia lam bai (Join Attempt) qua POST /api/play/join
    print("\n[2] Bat dau luot lam bai (Join Attempt) qua POST /api/play/join...")
    payload = {
        "code": code,
        "name": "Tester_Smoke",
        "device_id": "Smoke_Device_001"
    }
    status, join_res = request_json(f"{BASE_URL}/api/play/join", method="POST", data=payload)
    print(f"--> Status: {status} | Response: {join_res}")

    if status in (200, 201):
        token_str = join_res.get("attempt_token")
        print(f"\n[V] THAM GIA LAM BAI THANH CONG! Token phien: {token_str}")


        if token_str:
            # 3. Lay trang thai bai lam qua token
            print(f"\n[3] Lay trang thai bai lam qua GET /api/play/{token_str}/state...")
            st, state_res = request_json(f"{BASE_URL}/api/play/{token_str}/state")
            print(f"--> Status: {st} | Response: {state_res}")

    print("\n=== HOAN THANH KIEM TRA KET NOI LUONG LAM BAI ===")

if __name__ == "__main__":
    main()