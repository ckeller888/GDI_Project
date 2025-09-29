import React, { useEffect, useRef, useState } from "react";
import Map from "ol/Map.js";
import View from "ol/View.js";
import { Projection } from "ol/proj";
import GeoJSON from "ol/format/GeoJSON.js";
import { bbox as bboxStrategy } from "ol/loadingstrategy.js";
import { Vector as VectorSource, OSM } from "ol/source.js";
import { Tile as TileLayer, Vector as VectorLayer } from "ol/layer.js";
import TileWMS from "ol/source/TileWMS.js";
import Overlay from "ol/Overlay.js";
import { Style, Icon } from "ol/style.js";
import { Draw } from "ol/interaction.js";
import "ol/ol.css";

const OpenlayersMap = () => {
  const mapRef = useRef();
  const popupRef = useRef();

  const [mapInstance, setMapInstance] = useState(null);
  const [baseLayers, setBaseLayers] = useState({});
  const [baseLayer, setBaseLayer] = useState("swisstopo");
  const [drawInteraction, setDrawInteraction] = useState(null);

  //  Hintergrund-Layer definieren 
  const createBaseLayers = () => {
    return {
      swisstopo: new TileLayer({
        visible: true,
        source: new TileWMS({
          url: "https://wms.geo.admin.ch/",
          crossOrigin: "anonymous",
          attributions:
            '© <a href="http://www.geo.admin.ch/internet/geoportal/en/home.html">geo.admin.ch</a>',
          params: {
            LAYERS: "ch.swisstopo.pixelkarte-grau-pk1000.noscale",
            FORMAT: "image/jpeg",
          },
          serverType: "mapserver",
        }),
      }),
      orthofoto: new TileLayer({
        visible: false,
        source: new TileWMS({
          url: "https://wms.geo.admin.ch/",
          crossOrigin: "anonymous",
          params: {
            LAYERS: "ch.swisstopo.swissimage",
            FORMAT: "image/jpeg",
          },
          serverType: "mapserver",
        }),
      }),
      osm: new TileLayer({
        visible: false,
        source: new OSM(),
      }),
    };
  };

  useEffect(() => {
    const layers = createBaseLayers();
    setBaseLayers(layers);

    //  Daten-Layer 
    const vectorSource = new VectorSource({
      format: new GeoJSON(),
      url: "http://localhost:8000/getPoints",
      strategy: bboxStrategy,
    });

    const pointStyle = (feature) => {
      const besucht = feature.get("besucht");
      const iconUrl =
        besucht === "ja" ? "/icons/marker_green.svg" : "/icons/marker_red.svg";
      return new Style({
        image: new Icon({
          anchor: [0.5, 1],
          src: iconUrl,
          scale: 0.3,
        }),
      });
    };

    const vectorLayer = new VectorLayer({
      source: vectorSource,
      style: pointStyle,
    });

    // Popup 
    const popupOverlay = new Overlay({
      element: popupRef.current,
      positioning: "bottom-center",
      stopEvent: false,
      offset: [0, -10],
    });

    const map = new Map({
      target: mapRef.current,
      layers: [layers.swisstopo, layers.orthofoto, layers.osm, vectorLayer],
      view: new View({
        center: [2645000, 1187890],
        zoom: 8.9,
        projection: new Projection({
          code: "EPSG:2056",
          units: "m",
        }),
      }),
      overlays: [popupOverlay],
    });

    //  Popup bei Klick 
    map.on("singleclick", (evt) => {
      const feature = map.forEachFeatureAtPixel(evt.pixel, (f) => f);
      if (feature) {
        const props = feature.getProperties();

        popupRef.current.innerHTML = `
          <div style="background:white; padding:10px; border-radius:8px; box-shadow:0 2px 6px rgba(0,0,0,0.3); min-width:200px;">
            <strong>${props.name || "Unbenannt"}</strong><br/>
            <span style="color:#666;">Adresse: ${props.adresse || "-"}</span><br/>
            <span style="color:#666;">Besucht: ${props.besucht || "-"}</span><br/>
            <span style="color:#666;">Datum: ${props.datum || "-"}</span><br/>
            ${props.foto ? `<img src="${props.foto}" style="max-width:100%; border-radius:6px;"/>` : ""}
            ${props.bemerkungen ? `<span style="color:#666;">${props.bemerkungen.replace(/\n/g,"<br>")}</span>` : ""}
          </div>
        `;
        popupOverlay.setPosition(evt.coordinate);
      } else {
        popupOverlay.setPosition(undefined);
      }
    });

    setMapInstance(map);

    return () => map.setTarget(null);
  }, []);

  //  Layer wechseln 
  const handleLayerChange = (e) => {
    const selected = e.target.value;
    Object.entries(baseLayers).forEach(([key, layer]) => {
      layer.setVisible(key === selected);
    });
    setBaseLayer(selected);
  };

  //  Punkt hinzufügen 
  const startAddPoint = () => {
    if (!mapInstance) return;

    // Alte Draw-Interaction entfernen
    if (drawInteraction) mapInstance.removeInteraction(drawInteraction);

    const vectorLayer = mapInstance.getLayers().item(3);
    const draw = new Draw({ source: vectorLayer.getSource(), type: "Point" });

    draw.on("drawend", (evt) => {
      const coords = evt.feature.getGeometry().getCoordinates();

      const name = prompt("Name des Fotopoints:");
      const adresse = prompt("Adresse:");
      const datum = prompt("Datum (YYYY-MM-DD):");
      // const besucht = confirm("Wurde der Punkt schon besucht?") ? 1 : 0;
      const infos = prompt("Infos zum Punkt");

      fetch("http://localhost:8000/getPoints", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          adresse,
          datum,
          besucht,
          infos,
          x: coords[0],
          y: coords[1],
        }),
      })
        .then((res) => res.json())
        .then((data) => {
          alert(`Punkt hinzugefügt mit GID ${data.gid}`);
          vectorLayer.getSource().refresh();
        })
        .catch((err) => console.error(err));
    });

    mapInstance.addInteraction(draw);
    setDrawInteraction(draw);
  };

  return (
    <div style={{ width: "100%", height: "100vh", position: "relative" }}>
      <div
        style={{
          position: "absolute",
          top: 10,
          left: 10,
          zIndex: 1000,
          background: "white",
          padding: "5px 10px",
          borderRadius: "4px",
          boxShadow: "0 2px 6px rgba(0,0,0,0.3)",
        }}
      >
        <label>
          Layer:{" "}
          <select value={baseLayer} onChange={handleLayerChange}>
            <option value="osm">OpenStreetMap</option>
            <option value="swisstopo">Swisstopo Grau</option>
            <option value="orthofoto">Orthofoto</option>
          </select>
        </label>
        <br />
        <button style={{ marginTop: "5px" }} onClick={startAddPoint}>
          Punkt hinzufügen
        </button>
      </div>

      <div ref={mapRef} style={{ width: "100%", height: "100%" }} />
      <div ref={popupRef} style={{ position: "absolute" }} />
    </div>
  );
};

export default OpenlayersMap;
