export default function MobileCardList({ data = [], renderCard }) {
  if (!data.length) return null;

  return (
    <div className="hidden-desktop flex flex-col gap-md">
      {data.map(renderCard)}
    </div>
  );
}
