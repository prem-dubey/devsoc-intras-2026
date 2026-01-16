import SourceList from "./SourceList";

export default function Message({ message }) {
  return (
    <div className={`message ${message.role}`}>
      <div className="text">{message.text}</div>

      {message.sources && message.sources.length > 0 && (
        <SourceList sources={message.sources} />
      )}
    </div>
  );
}
