import React from 'react';
import { 
  Segment, 
  Header, 
  List, 
  Icon, 
  Label,
  Button
} from 'semantic-ui-react';

const SearchSuggestions = ({ analytics, onSuggestionClick }) => {
  const suggestions = [
    { text: "machine learning algorithms", type: "popular", count: 156 },
    { text: "research methodology", type: "trending", count: 89 },
    { text: "data visualization", type: "popular", count: 234 },
    { text: "python programming", type: "recent", count: 67 },
    { text: "statistical analysis", type: "trending", count: 123 }
  ];

  const getSuggestionColor = (type) => {
    switch (type) {
      case 'popular': return 'blue';
      case 'trending': return 'green';
      case 'recent': return 'orange';
      default: return 'grey';
    }
  };

  const getSuggestionIcon = (type) => {
    switch (type) {
      case 'popular': return 'star';
      case 'trending': return 'arrow up';
      case 'recent': return 'clock';
      default: return 'search';
    }
  };

  return (
    <Segment>
      <Header as="h4">
        <Icon name="lightbulb" />
        Search Suggestions
      </Header>
      
      <List divided relaxed>
        {suggestions.map((suggestion, index) => (
          <List.Item 
            key={index}
            as="a"
            onClick={() => onSuggestionClick(suggestion.text)}
            className="search-suggestion-item"
          >
            <List.Content>
              <List.Header>
                <Icon 
                  name={getSuggestionIcon(suggestion.type)}
                  color={getSuggestionColor(suggestion.type)}
                />
                {suggestion.text}
              </List.Header>
              <List.Description>
                <Label 
                  size="mini" 
                  color={getSuggestionColor(suggestion.type)}
                >
                  {suggestion.type}
                </Label>
                <span className="search-count">
                  {suggestion.count} searches
                </span>
              </List.Description>
            </List.Content>
          </List.Item>
        ))}
      </List>
    </Segment>
  );
};

export default SearchSuggestions; 