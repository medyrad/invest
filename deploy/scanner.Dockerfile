FROM public.ecr.aws/docker/library/python:3.14.10-slim-bookworm@sha256:1faf2343e747208b2a36e5f2b5ff908ec3b2d0078a6a7bfe73b535698fe83909
COPY root/usr/local/lib/*.so* /usr/local/lib/
COPY root/usr/local/bin/clamscan root/usr/local/bin/freshclam root/usr/local/bin/sigtool /usr/local/bin/
COPY root/usr/local/sbin/clamd /usr/local/sbin/
COPY root/usr/local/etc/certs/ /usr/local/etc/certs/
RUN ldconfig && useradd --uid 10001 --create-home invest
USER invest
ENTRYPOINT ["/usr/local/sbin/clamd"]
