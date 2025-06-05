import React from 'react';
import Modal from '../common/Modal';

interface SuggestedTitlesModalProps {
  isOpen: boolean;
  onClose: () => void;
  titles: string[];
  onSelectTitle: (title: string) => void;
}

const SuggestedTitlesModal: React.FC<SuggestedTitlesModalProps> = ({
  isOpen,
  onClose,
  titles,
  onSelectTitle,
}) => {
  const handleTitleClick = (title: string) => {
    onSelectTitle(title);
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Suggested Titles">
      <div style={{ padding: '20px' }}>
        <ul style={{ listStyleType: 'none', padding: 0, margin: 0 }}>
          {titles.map((title, index) => (
            <li
              key={index}
              onClick={() => handleTitleClick(title)}
              style={{
                padding: '10px 0',
                cursor: 'pointer',
                borderBottom: '1px solid #eee',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#f9f9f9')}
              onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
            >
              {title}
            </li>
          ))}
        </ul>
      </div>
    </Modal>
  );
};

export default SuggestedTitlesModal;
