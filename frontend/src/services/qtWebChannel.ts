type QtWebChannel = {
  objects: Record<string, unknown>;
};

const WEB_CHANNEL_ERROR = "Qt WebChannel is unavailable.";

let channelPromise: Promise<QtWebChannel> | null = null;

export const getQtWebChannel = () => {
  channelPromise ??= new Promise<QtWebChannel>((resolve, reject) => {
    if (!window.qt?.webChannelTransport || !window.QWebChannel) {
      reject(new Error(WEB_CHANNEL_ERROR));
      return;
    }

    new window.QWebChannel(window.qt.webChannelTransport, (channel) => {
      resolve(channel as QtWebChannel);
    });
  });

  return channelPromise;
};

/** @internal Clear the cached channel between isolated bridge tests. */
export const resetQtWebChannelForTests = () => {
  channelPromise = null;
};
