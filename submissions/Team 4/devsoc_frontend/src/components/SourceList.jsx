export default function SourceList({ sources }) {
  return (
    <div className="sources">
      <strong>Sources:</strong>
      <ul>
        {sources.map((src, idx) => (
          <li key={idx}>
            <a href={src} target="_blank" rel="noreferrer">
              {src}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}
