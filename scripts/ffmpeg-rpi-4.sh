#!/bin/bash

TMPDIR="$(mktemp -d)"

function cleanup {
  rm -rf "${TMPDIR}"
}

trap cleanup EXIT

# Install Dependencies
sudo apt-get update -qq && sudo apt-get -y install \
  autoconf \
  automake \
  build-essential \
  cmake \
  doxygen \
  git \
  graphviz \
  imagemagick \
  libasound2-dev \
  libass-dev \
  libavcodec-dev \
  libavdevice-dev \
  libavfilter-dev \
  libavformat-dev \
  libavutil-dev \
  libfreetype6-dev \
  libgmp-dev \
  libmp3lame-dev \
  libopencore-amrnb-dev \
  libopencore-amrwb-dev \
  libopus-dev \
  librtmp-dev \
  libsdl2-dev \
  libsdl2-image-dev \
  libsdl2-mixer-dev \
  libsdl2-net-dev \
  libsdl2-ttf-dev \
  libsnappy-dev \
  libsoxr-dev \
  libssh-dev \
  libssl-dev \
  libtool \
  libv4l-dev \
  libva-dev \
  libvdpau-dev \
  libvo-amrwbenc-dev \
  libvorbis-dev \
  libwebp-dev \
  libx264-dev \
  libx265-dev \
  libxcb-shape0-dev \
  libxcb-shm0-dev \
  libxcb-xfixes0-dev \
  libxcb1-dev \
  libxml2-dev \
  lzma-dev \
  meson \
  nasm \
  pkg-config \
  python3-dev \
  python3-pip \
  texinfo \
  wget \
  yasm \
  zlib1g-dev


# To disable remove --enable-libfdk-aac
#git clone --depth 1 https://github.com/mstorsjo/fdk-aac "${TMPDIR}/fdk-aac" && cd "${TMPDIR}/fdk-aac" \
#  && autoreconf -fiv \
#  && ./configure \
#  && make -j$(nproc) \
#  && sudo make install

# To disable remove --enable-libdav1d
git clone --depth 1 https://code.videolan.org/videolan/dav1d.git "${TMPDIR}/dav1d" && mkdir "${TMPDIR}/dav1d/build" && cd "${TMPDIR}/dav1d/build" \
  && meson .. \
  && ninja \
  && sudo ninja install

# To disable remove --enable-libkvazaar
#git clone --depth 1 https://github.com/ultravideo/kvazaar.git "${TMPDIR}/kvazaar" && cd "${TMPDIR}/kvazaar" \
#  && ./autogen.sh \
#  && ./configure \
#  && make -j$(nproc) \
#  && sudo make install

# To disable remove --enable-libvpx
#git clone --depth 1 https://chromium.googlesource.com/webm/libvpx "${TMPDIR}/libvpx" && cd "${TMPDIR}/libvpx" \
#  && ./configure --disable-examples \
#  && make -j$(nproc) \
#  && sudo make install

# To disable remove --enable-libaom
#git clone --depth 1 https://aomedia.googlesource.com/aom "${TMPDIR}/aom" && mkdir "${TMPDIR}/aom/aom_build" && cd "${TMPDIR}/aom/aom_build" \
#  && git checkout $(git rev-list -1 --before="Dec 15 2019" master) \
#  && cmake -G "Unix Makefiles" AOM_SRC -DENABLE_NASM=on -DPYTHON_EXECUTABLE="$(which python3)" -DCMAKE_C_FLAGS="-mfpu=vfp -mfloat-abi=hard" .. \
#  && sed -i 's/ENABLE_NEON:BOOL=ON/ENABLE_NEON:BOOL=OFF/' CMakeCache.txt \
#  && make -j$(nproc) \
#  && sudo make install

# Compile FFmpeg
#git clone --depth 1 https://github.com/FFmpeg/FFmpeg.git "${TMPDIR}/FFmpeg" && cd "${TMPDIR}/FFmpeg" \
#  && ./configure \
#    --extra-cflags="-I/usr/local/include" \
 #   --extra-ldflags="-L/usr/local/lib" \
#    --extra-libs="-lpthread -lm" \
#    --arch=armel \
#    --enable-gmp \
#    --enable-gpl \
#    --enable-libaom \
#    --enable-libass \
#    --enable-libdav1d \
#    --enable-libfdk-aac \
#    --enable-libfreetype \
#    --enable-libkvazaar \
#    --enable-libmp3lame \
#    --enable-libopencore-amrnb \
#    --enable-libopencore-amrwb \
#    --enable-libopus \
#    --enable-librtmp \
#    --enable-libsnappy \
#    --enable-libsoxr \
#    --enable-libssh \
#    --enable-libvorbis \
#    --enable-libvpx \
#    --enable-libwebp \
#    --enable-libx264 \
#    --enable-libx265 \
#    --enable-libxml2 \
#    --enable-mmal \
#    --enable-nonfree \
#    --enable-omx \
#    --enable-omx-rpi \
#    --enable-version3 \
#    --target-os=linux \
#    --enable-pthreads \
#    --enable-openssl \
#    --enable-hardcoded-tables \
#    --extra-ldflags="-latomic" \
#  && make -j$(nproc) \
#  && sudo make install
