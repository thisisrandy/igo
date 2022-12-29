import React, { useCallback } from "react";
import { useDispatch, useSelector } from "react-redux";
import { ACCEPT, REJECT } from "../constants/GameActionTypes";
import { INITIATOR, REQUEST_TYPE } from "../constants/RequestKeys";
import {
  KEYS,
  PENDING_REQUEST,
  STATUS,
  YOUR_COLOR,
} from "../constants/StateKeys";
import { send } from "@giantmachines/redux-websocket";
import { ACTION_TYPE, KEY, TYPE } from "../constants/OutgoingMessageKeys";
import { GAME_ACTION } from "../constants/OutgoingMessageTypes";
import { MARK_DEAD, DRAW, TALLY_SCORE } from "../constants/RequestType";
import { REQUEST_PENDING } from "../constants/GameStatus";
import { capitalizeFirstLetter } from "../utils";
import YesNoDialog from "./YesNoDialog";
import { GAME } from "../constants/ReducerKeys";

function RequestResponseDialog({ zIndex }) {
  const {
    [STATUS]: gameStatus,
    [PENDING_REQUEST]: pendingRequest,
    [YOUR_COLOR]: yourColor,
    [KEYS]: keys,
  } = useSelector((state) => state[GAME]);
  const dispatch = useDispatch();

  const getDialogOpen = useCallback(() => {
    if (gameStatus !== REQUEST_PENDING) return false;
    return pendingRequest[INITIATOR] !== yourColor;
  }, [gameStatus, pendingRequest, yourColor]);

  const getRequestText = useCallback(() => {
    if (gameStatus !== REQUEST_PENDING) return "";
    const color = capitalizeFirstLetter(pendingRequest[INITIATOR]);
    switch (pendingRequest[REQUEST_TYPE]) {
      case MARK_DEAD:
        return (
          <React.Fragment>
            {color} has marked a group as dead. Do you concur? If yes, the group
            will be removed and counted as prisoner(s). If no, you will be
            returned to play to resolve the disagreement.{" "}
            <em>
              Hint: If this dialog is obscuring your view of the dead group,
              simply grab it by the top and drag it out of the way
            </em>
          </React.Fragment>
        );
      case DRAW:
        return (
          <React.Fragment>
            {color} has requested a draw. Do you accept?
          </React.Fragment>
        );
      case TALLY_SCORE:
        return (
          <React.Fragment>
            {color} has indicated that they are ready to tally the score. Do you
            concur? If yes, territory will be calculated and the game will end.
            If no, you will be returned to the endgame to resolve the
            disagreement
          </React.Fragment>
        );
      default:
        throw new TypeError(
          `Unknown request type ${pendingRequest[REQUEST_TYPE]} encountered`
        );
    }
  }, [gameStatus, pendingRequest]);

  const accept = () => {
    dispatch(
      send({
        [TYPE]: GAME_ACTION,
        [KEY]: keys[yourColor],
        [ACTION_TYPE]: ACCEPT,
      })
    );
  };
  const reject = () => {
    dispatch(
      send({
        [TYPE]: GAME_ACTION,
        [KEY]: keys[yourColor],
        [ACTION_TYPE]: REJECT,
      })
    );
  };

  return (
    <YesNoDialog
      zIndex={zIndex}
      open={getDialogOpen()}
      title="Request"
      yesHandler={accept}
      noHandler={reject}
    >
      {getRequestText()}
    </YesNoDialog>
  );
}

export default RequestResponseDialog;
