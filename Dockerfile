FROM kunalg106/cuda121

ENV BLENDER_PATH=/work/blender-4.5.4-linux-x64/blender
ENV BLENDER_PYTHON=/work/blender-4.5.4-linux-x64/4.5/python/bin/python3.11

RUN mkdir -p /work && \
    wget -q https://download.blender.org/release/Blender4.5/blender-4.5.4-linux-x64.tar.xz -O /tmp/blender.tar.xz && \
    tar -xf /tmp/blender.tar.xz -C /work/ && \
    rm /tmp/blender.tar.xz

RUN conda create -n interioragent python=3.12 -y
RUN /opt/conda/envs/interioragent/bin/pip install numpy matplotlib trimesh scipy tqdm sceneprogllm sceneprogexec
RUN /opt/conda/envs/interioragent/bin/sceneprogexec install sceneprogllm

RUN apt-get update && apt-get install -y \
    libgl1 \
    libglx-mesa0 \
    libegl1 \
    libxrender1 \
    libxi6 \
    libxkbcommon0 \
    libsm6 \
    libice6 \
    && rm -rf /var/lib/apt/lists/*