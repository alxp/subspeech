import contextlib, wave

def wavLen(fname):
    with contextlib.closing(wave.open(fname, 'r')) as f:
        frames=f.getnframes()
        rate=f.getframerate()
        duration=frames/float(rate)
        return int(duration * 1000) # Milliseconds
