type QtWebChannelObjects = Record<string, unknown>;

type QtWebChannelInstance = {
  objects: QtWebChannelObjects;
};

type QtWebChannelConstructor = new (
  transport: unknown,
  callback: (channel: QtWebChannelInstance) => void,
) => void;

interface Window {
  qt?: {
    webChannelTransport: unknown;
  };
  QWebChannel?: QtWebChannelConstructor;
}
