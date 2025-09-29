import { NavLink } from "react-router";

function NavButton({ path, children }) {
  return (
    <NavLink
      to={path}
      style={({ isActive }) => ({
        // display: "inline-block",
        // margin: ".5em 1em",
        // color: isActive ? "dodgerblue" : "black",
      })}
    >
      {children}
    </NavLink>
  );
}

function Header() {
  return (
    <>
      <h1 className="title">
          <img src="./grandtour_logo.svg" className="logo" />
        Grand Tour Foto-Spots
      </h1>
      {/* <h2>
        <NavButton path="openlayers">
          OpenLayers
        </NavButton>
        <NavButton path="maplibre">
          MapLibre (Reactive)
        </NavButton>
        <NavButton path="spatialanalysis">Spatial Analysis</NavButton>
        <NavButton path="geotiff">Cloud-optimized GeoTIFF</NavButton>
      </h2> */}
    </>
  );
}
export default Header;
