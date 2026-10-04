import { MapContainer, Marker, Polyline, Popup, TileLayer, useMap } from "react-leaflet";
import { useEffect } from "react";
import L from "leaflet";

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png",
  iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
});

function Fit({ points }) {
  const map = useMap();
  useEffect(() => {
    map.fitBounds(points, { padding: [35, 35] });
  }, [map, points]);
  return null;
}

export default function RouteMap({ plan }) {
  const coords = plan.route.geometry.coordinates.map(([lon, lat]) => [lat, lon]);
  const markers = [
    ["Current", plan.locations.current],
    ["Pickup", plan.locations.pickup],
    ["Dropoff", plan.locations.dropoff],
  ];
  return (
    <>
      <div className="map-wrap">
        <MapContainer center={coords[0]} zoom={5} scrollWheelZoom>
          <TileLayer attribution="&copy; OpenStreetMap contributors" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          <Polyline positions={coords} weight={5} />
          {markers.map(([label, p]) => (
            <Marker key={label} position={[p.lat, p.lon]}>
              <Popup><strong>{label}</strong><br />{p.name}</Popup>
            </Marker>
          ))}
          <Fit points={coords} />
        </MapContainer>
      </div>
      <div className="route-points">
        {markers.map(([label, p]) => <div key={label}><span>{label}</span><strong>{p.name}</strong></div>)}
      </div>
    </>
  );
}
