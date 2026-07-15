FROM kunalg106/cuda121

# Blender lives OUTSIDE /work: the repo is volume-mounted at /work, and mounting
# over the directory that holds Blender would shadow it (the original trap).
ENV BLENDER_PATH=/opt/blender-4.5.4-linux-x64/blender
ENV BLENDER_PYTHON=/opt/blender-4.5.4-linux-x64/4.5/python/bin/python3.11

RUN wget -q https://download.blender.org/release/Blender4.5/blender-4.5.4-linux-x64.tar.xz -O /tmp/blender.tar.xz && \
    tar -xf /tmp/blender.tar.xz -C /opt/ && \
    rm /tmp/blender.tar.xz

RUN conda create -n interioragent python=3.12 -y
COPY requirements.txt /tmp/requirements.txt
RUN /opt/conda/envs/interioragent/bin/pip install -r /tmp/requirements.txt
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

# Usage: mount the repo (with datasets extracted) at /work and run from there:
#   docker build -t interioragent .
#   docker run -it -v "$PWD":/work -w /work -e OPENAI_API_KEY interioragent bash
