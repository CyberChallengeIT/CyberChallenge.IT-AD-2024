export default class HttpError extends Error {
  constructor(code, message) {
    super(`HTTP Error \`${code}\`: ${message}`);
    this.code = code;
    this.message = message;
  }
}

