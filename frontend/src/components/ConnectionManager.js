import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { connect } from "@giantmachines/redux-websocket";
import { RECONNECT_INTERVAL_MS } from "../constants/ConnectionSettings";
import { CONNECTED } from "../constants/StateKeys";
import { GAME } from "../constants/ReducerKeys";

function ConnectionManager() {
  const { [CONNECTED]: connected } = useSelector((state) => state[GAME]);
  const dispatch = useDispatch();
  const serverUri = process.env.REACT_APP_GAME_SERVER_URI;

  // NOTE: as noted in middleware setup, redux-websocket for doesn't attempt to
  // reconnect if the first connection attempt fails, instead opting to only
  // reconnect a previously successful connection on certain configurable
  // conditions. As this doesn't fully meet our needs, it's easier just to turn
  // its mechanisms off and handle reconnection ourselves via an effect
  useEffect(() => {
    if (!connected) {
      const do_connect = () => dispatch(connect(serverUri));
      do_connect();
      const interval = setInterval(do_connect, RECONNECT_INTERVAL_MS);
      return () => clearInterval(interval);
    }
  }, [connected, dispatch, serverUri]);

  return null;
}

export default ConnectionManager;
