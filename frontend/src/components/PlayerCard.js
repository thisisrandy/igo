import { Paper, Typography } from "@material-ui/core";
import clsx from "clsx";
import React, { useCallback } from "react";
import { useSelector } from "react-redux";
import { WHITE } from "../constants/Colors";
import {
  KEYS,
  KOMI,
  PRISONERS,
  TERRITORY,
  YOUR_COLOR,
  OPPONENT_CONNECTED,
  TURN,
} from "../constants/StateKeys";
import { useStyles } from "../hooks/useStyles";
import black from "../images/black.png";
import white from "../images/white.png";
import StarIcon from "@material-ui/icons/Star";
import { GAME } from "../constants/ReducerKeys";

function PlayerCard({ color, joinedToGame, playing }) {
  const classes = useStyles();
  const {
    [YOUR_COLOR]: yourColor,
    [PRISONERS]: prisoners,
    [TERRITORY]: territory,
    [KOMI]: komi,
    [KEYS]: keys,
    [OPPONENT_CONNECTED]: opponentConnected,
    [TURN]: turn,
  } = useSelector((state) => state[GAME]);

  const isThisMe = useCallback(() => {
    return color === yourColor;
  }, [color, yourColor]);

  return (
    <Paper
      className={clsx(
        classes.PlayerCardContainer,
        isThisMe()
          ? classes.PlayerCardSelf
          : joinedToGame && !opponentConnected
          ? classes.PlayerCardOpponentNotConnected
          : classes.PlayerCardNeutral
      )}
      variant="outlined"
    >
      <span className={classes.PlayerCardSpan}>
        <Paper className={classes.PlayerCardSubContainer}>
          <img
            src={color === WHITE ? white : black}
            alt={`player stone display for ${color}`}
            className={classes.PlayerStoneImage}
          />
        </Paper>
        <Paper
          className={classes.PlayerCardSubContainer}
          style={{ flexGrow: 1 }}
        >
          <div className={classes.PlayerCardScoreColumn}>
            <Typography>Prisoners:</Typography>
            <Typography>Territory:</Typography>
            <Typography>Total Score:</Typography>
          </div>
          <div className={classes.PlayerCardScoreColumn}>
            <Typography aria-label={`prisoner count for ${color}`}>
              {joinedToGame ? prisoners[color] : "-"}
            </Typography>
            <Typography aria-label={`territory count for ${color}`}>
              {joinedToGame ? territory[color] : "-"}
            </Typography>
            <Typography aria-label={`total score for ${color}`}>
              {joinedToGame
                ? prisoners[color] +
                  territory[color] +
                  (color === WHITE ? komi : 0)
                : "-"}
            </Typography>
          </div>
        </Paper>
      </span>
      <Paper className={classes.PlayerCardKeyContainer}>
        {joinedToGame && playing && turn === color && (
          <StarIcon aria-label={`it's ${color}'s turn`} />
        )}
        <Typography
          aria-label={`player key for ${color}`}
          variant="caption"
          style={{ marginLeft: joinedToGame ? 5 : 0 }}
        >
          Player Key: {joinedToGame ? keys[color] : "-"}
        </Typography>
        {joinedToGame && (
          <Typography
            aria-label={`connection status for ${color}`}
            variant="caption"
            style={{ marginLeft: 5 }}
          >
            {isThisMe()
              ? "(you)"
              : opponentConnected
              ? "(connected)"
              : "(not connected)"}
          </Typography>
        )}
      </Paper>
    </Paper>
  );
}

export default PlayerCard;
