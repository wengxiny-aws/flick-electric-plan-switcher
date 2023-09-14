import sys
import switch

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python switch.py email password plan(flat|off_peak|superflat)")
        sys.exit(1)

    try:
        switch.switch(sys.argv[1], sys.argv[2], sys.argv[3])
    except Exception as e: 
        print(e)