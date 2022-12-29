import { send } from "@giantmachines/redux-websocket/dist";
import {
  Button,
  Card,
  CardActions,
  CardContent,
  CardHeader,
  TextField,
} from "@material-ui/core";
import React, { useEffect, useRef, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { CHAT_MESSAGE_FIELD } from "../constants/Ids";
import { KEY, MESSAGE, TYPE } from "../constants/OutgoingMessageKeys";
import { CHAT_MESSAGE } from "../constants/OutgoingMessageTypes";
import { KEYS, YOUR_COLOR } from "../constants/StateKeys";
import { useStyles } from "../hooks/useStyles";
import ChatDisplay from "./ChatDisplay";
import { GAME } from "../constants/ReducerKeys";

function ChatCard({ joinedToGame }) {
  const classes = useStyles();
  const { [YOUR_COLOR]: yourColor, [KEYS]: keys } = useSelector(
    (state) => state[GAME]
  );
  const dispatch = useDispatch();

  const [message, setMessage] = useState("");
  const sendMessageHandler = () => {
    dispatch(
      send({
        [TYPE]: CHAT_MESSAGE,
        [KEY]: keys[yourColor],
        [MESSAGE]: message,
      })
    );
    setMessage("");
  };

  const [canSend, setCanSend] = useState(false);
  useEffect(() => {
    setCanSend(joinedToGame && !!message);
  }, [joinedToGame, message]);

  const inputRef = useRef();
  const focusInput = () => inputRef.current.focus();

  return (
    <Card className={classes.ChatCard}>
      <CardHeader title="Chat" titleTypographyProps={{ variant: "h5" }} />
      <CardContent className={classes.ChatDisplayContainer}>
        <ChatDisplay {...{ focusInput }} />
      </CardContent>
      <CardActions disableSpacing={true} className={classes.ChatCardActions}>
        <TextField
          // NOTE: we use an id here because it is necessary as something for
          // the label "for" attribute to point to. ARIA (and testing) breaks
          // otherwise
          id={CHAT_MESSAGE_FIELD}
          label="Chat message"
          variant="outlined"
          multiline
          rows={3}
          className={classes.ChatInput}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          disabled={!joinedToGame}
          onKeyPress={(e) => {
            if (e.key === "Enter" && canSend) {
              e.preventDefault();
              sendMessageHandler();
            }
          }}
          inputRef={inputRef}
        />
        <Button
          variant="contained"
          className={classes.ChatButton}
          disabled={!canSend}
          onClick={sendMessageHandler}
        >
          Send
        </Button>
      </CardActions>
    </Card>
  );
}

export default ChatCard;
