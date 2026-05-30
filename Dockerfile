FROM eclipse-temurin:21-jre-jammy AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    XDG_DATA_HOME=/data \
    PYTHONPATH=/app/src:/app/src/backend

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        git \
        python-is-python3 \
        python3-pip \
        python3-gi \
        gir1.2-gtk-3.0 \
        gir1.2-webkit2-4.0 \
        libgtk-3-0 \
        libwebkit2gtk-4.0-37 \
        xvfb \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /data/letsplaymc/java/bin /data/letsplaymc/git/cmd \
    && ln -sf /opt/java/openjdk/bin/java /data/letsplaymc/java/bin/java \
    && ln -sf /usr/bin/git /data/letsplaymc/git/cmd/git

FROM base AS deps

COPY requirements.txt .
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

FROM deps AS build

COPY src ./src
RUN python -m compileall -q src

FROM build AS test

RUN python -m compileall -q src \
    && python -c "from backend.path.path import get_os, get_java_path, get_git_path; print(get_os()); assert get_java_path().exists(); assert get_git_path().exists()" \
    && python -c "from backend.server.project import resolve_version; assert resolve_version('paper', '1.20.1') == '1.20.1'"

FROM deps AS deploy

COPY --from=build /app/src ./src

CMD ["python", "src/main.py"]
