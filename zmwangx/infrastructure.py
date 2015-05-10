#!/usr/bin/env python3

"""Shared testing infrastructure."""

from contextlib import contextmanager
import io
import os
import shutil
import sys
import tempfile


class NormalizedStringIO(io.StringIO):
    """StringIO, with write operations normalized to unicode."""

    def __init__(self, buffer=None):
        super(NormalizedStringIO, self).__init__(buffer)

    @staticmethod
    def normalized(s):
        """Normalize string to str."""
        if isinstance(s, str):
            return s
        elif isinstance(s, bytes):
            return s.decode('utf-8')
        else:
            raise ValueError("expected str or bytes, got %s" %
                             type(s).__name__)

    def write(self, s):
        super().write(self.normalized(s))

    def writelines(self,lines):
        lines = [self.normalized(line) for line in lines]
        super().writelines(lines)


class Tee(io.TextIOBase):
    """Duplicate all output to a text stream on a StringIO stream.

    This class implements a write-only (unreadable, unseekable)
    io.TextIOBase based on a given io.TextIOBase stream, and duplicates
    all write operations on a intrinsic StringIO stream. The class can
    be used to tee output, e.g., sys.stderr, to a string. To use this
    class, make normal calls as if it is the base stream, with the
    exception that one can call getvalue() as if it is also a StringIO.

    """

    def __init__(self, textio):
        if not textio.writable():
            raise io.UnsupportedOperation("not writable")
        self._textio = textio
        self._stringio = NormalizedStringIO()

    def close(self):
        self._textio.close()
        self._stringio.close()

    @property
    def closed(self):
        return self._textio.closed

    def detach(self):
        return self._textio.detach()

    @property
    def encoding(self):
        return self._textio.encoding

    @property
    def errors(self):
        return self._textio.errors

    def fileno(self):
        return self._textio.fileno()

    def flush(self):
        self._textio.flush()
        self._stringio.flush()

    def getvalue(self):
        return self._stringio.getvalue()

    def isatty(self):
        return self._textio.isatty()

    @staticmethod
    def read(size):
        raise io.UnsupportedOperation("not readable")

    @staticmethod
    def readable():
        return False

    @staticmethod
    def readline(size=-1):
        raise io.UnsupportedOperation("not readable")

    @staticmethod
    def readlines(hint=-1):
        raise io.UnsupportedOperation("not readable")

    @staticmethod
    def seek(offset, whence=os.SEEK_SET):
        raise io.UnsupportedOperation("not seekable")

    @staticmethod
    def seekable():
        return False

    @staticmethod
    def tell():
        raise io.UnsupportedOperation("not seekable")

    @staticmethod
    def truncate(size=None):
        raise io.UnsupportedOperation("not seekable")

    @staticmethod
    def writable():
        return True

    def write(self, s):
        bytes_written = self._textio.write(s)
        self._stringio.write(s)
        return bytes_written

    def writelines(self, lines):
        self._textio.writelines(lines)
        self._stringio.writelines(lines)

    def __del__(self):
        del self._stringio


@contextmanager
def capture_stdout():
    """Single use context manager for capturing stdout in a StringIO.

    The negative effect is that some properties of the stream are
    changed, e.g., isatty().

    """

    saved_stdout = sys.stdout
    sys.stdout = NormalizedStringIO()
    yield
    sys.stdout = saved_stdout

@contextmanager
def capture_stderr():
    """Single use context manager for capturing stderr in a StringIO.

    The negative effect is that some properties of the stream are
    changed, e.g., isatty().

    """

    saved_stderr = sys.stderr
    sys.stderr = NormalizedStringIO()
    yield
    sys.stderr = saved_stderr

@contextmanager
def tee_stderr():
    """Single use context manager for teeing stderr to a StringIO.

    Unlike capture_stderr, sys.stderr keeps its original properties,
    except that it is no longer seekable.

    """

    saved_stderr = sys.stderr
    sys.stderr = Tee(sys.stderr)
    yield
    sys.stderr = saved_stderr

@contextmanager
def change_home():
    """Single use context manager for changing HOME to a temp directory.

    The temp directory will be empty.

    """

    if 'HOME' in os.environ:
        saved_home = os.environ['HOME']
    else:
        saved_home = None
    tmp_home = tempfile.mkdtemp()
    os.environ['HOME'] = tmp_home
    yield tmp_home
    shutil.rmtree(tmp_home)
    if saved_home is not None:
        os.environ['HOME'] = saved_home
