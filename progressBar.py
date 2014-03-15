import time
import sys

def progress(width, times):
    toolbar_width = width

    # setup toolbar
    sys.stdout.write("[%s]" % (" " * toolbar_width))
    sys.stdout.flush()
    sys.stdout.write("\b" * (toolbar_width + 1))
    # return to start of line, after '['

    for i in xrange(toolbar_width):
        time.sleep(times)  # do real work here
        # update the bar
        sys.stdout.write("=")
        sys.stdout.flush()

    sys.stdout.write("\n")

if __name__ == "__main__":
    progress(40, 0.5)
