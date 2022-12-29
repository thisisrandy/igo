import React from "react";
import ReactDOM from "react-dom";
import App from "./components/App";
import reportWebVitals from "./reportWebVitals";
import { Provider } from "react-redux";
import { createStore, applyMiddleware } from "redux";
import rootReducer from "./reducers";
import reduxWebsocket from "@giantmachines/redux-websocket";
import { persistStore } from "redux-persist";
import { PersistGate } from "redux-persist/integration/react";

// NOTE: redux-websocket for doesn't attempt to reconnect if the first
// connection attempt fails, instead opting to only reconnect a previously
// successful connection on certain configurable conditions. As this doesn't
// fully meet our needs, it's easier just to turn its mechanisms off and handle
// reconnection ourselves via an effect
const reduxWebsocketMiddleware = reduxWebsocket({
  deserializer: JSON.parse,
  reconnectOnClose: false,
  reconnectOnError: false,
});

const store = createStore(
  rootReducer,
  applyMiddleware(reduxWebsocketMiddleware)
);
const persistor = persistStore(store);

ReactDOM.render(
  <React.StrictMode>
    <Provider store={store}>
      <PersistGate loading={null} persistor={persistor}>
        <App />
      </PersistGate>
    </Provider>
  </React.StrictMode>,
  document.getElementById("root")
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
