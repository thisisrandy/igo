import { send } from "@giantmachines/redux-websocket";
import { useDispatch, useSelector } from "react-redux";
import { clearRejoinNeeded } from "../actions";
import { KEY, TYPE } from "../constants/OutgoingMessageKeys";
import { JOIN_GAME } from "../constants/OutgoingMessageTypes";
import {
  CONNECTED,
  KEYS,
  REJOIN_NEEDED,
  YOUR_COLOR,
} from "../constants/StateKeys";
import { GAME } from "../constants/ReducerKeys";

/**
 * Logic-only component to rejoin game on reconnect
 */
function GameRejoiner() {
  const {
    [KEYS]: keys,
    [YOUR_COLOR]: yourColor,
    [REJOIN_NEEDED]: rejoinNeeded,
    [CONNECTED]: connected,
  } = useSelector((state) => state[GAME]);
  const dispatch = useDispatch();

  if (connected && rejoinNeeded) {
    dispatch(send({ [TYPE]: JOIN_GAME, [KEY]: keys[yourColor] }));
    dispatch(clearRejoinNeeded());
  }

  return null;
}

export default GameRejoiner;
