import React from 'react';
import { 
  Segment, 
  Header, 
  List, 
  Icon, 
  Label,
  Button
} from 'semantic-ui-react';
import { formatDistanceToNow } from 'date-fns';

const SearchHistory = ({ history = [], onHistoryClick, onClearHistory }) => {
  if (history.length === 0) {
    return (
      <Segment>
        <Header as="h4">
          <Icon name="history" />
          Search History
        </Header>
        <p>No recent searches</p>
      </Segment>
    );
  }

  const getModeIcon = (mode) => {
    switch (mode) {
      case 'semantic': return 'brain';
      case 'similar': return 'clone';
      default: return 'search';
    }
  };

  const getModeColor = (mode) => {
    switch (mode) {
      case 'semantic': return 'blue';
      case 'similar': return 'purple';
      default: return 'green';
    }
  };

  return (
    <Segment>
      <Header as="h4">
        <Icon name="history" />
        Search History
        <Button 
          floated="right" 
          size="mini" 
          basic
          icon="trash"
          onClick={onClearHistory}
          title="Clear history"
        />
      </Header>
      
      <List divided relaxed size="small">
        {history.map((item, index) => (
          <List.Item 
            key={index}
            as="a"
            onClick={() => onHistoryClick(item)}
            className="search-history-item"
          >
            <List.Content>
              <List.Header>
                <Icon 
                  name={getModeIcon(item.mode)}
                  color={getModeColor(item.mode)}
                />
                {item.query.length > 30 ? 
                  `${item.query.substring(0, 30)}...` : 
                  item.query
                }
              </List.Header>
              <List.Description>
                <Label 
                  size="mini" 
                  color={getModeColor(item.mode)}
                >
                  {item.mode}
                </Label>
                <span className="result-count">
                  {item.results} results
                </span>
                <span className="search-time">
                  {formatDistanceToNow(new Date(item.timestamp), { addSuffix: true })}
                </span>
              </List.Description>
            </List.Content>
          </List.Item>
        ))}
      </List>
    </Segment>
  );
};

export default SearchHistory; 