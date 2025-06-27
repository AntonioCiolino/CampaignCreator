import React from 'react';
import ImageIcon from '@mui/icons-material/Image';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import DescriptionIcon from '@mui/icons-material/Description'; // For .txt
import ArticleIcon from '@mui/icons-material/Article'; // For .md or other documents
import FolderZipIcon from '@mui/icons-material/FolderZip';
import InsertDriveFileIcon from '@mui/icons-material/InsertDriveFile'; // Default
import AudiotrackIcon from '@mui/icons-material/Audiotrack';
import VideocamIcon from '@mui/icons-material/Videocam';
import CodeIcon from '@mui/icons-material/Code'; // For code files
import TableChartIcon from '@mui/icons-material/TableChart'; // For CSV/Excel

// Define a common style for icons if needed, or style via CSS
const iconStyle = { fontSize: '1.2rem', verticalAlign: 'middle' }; // Example style

export const getFileTypeIcon = (filename?: string, contentType?: string): React.ReactElement => {
  const extension = filename?.substring(filename.lastIndexOf('.') + 1).toLowerCase() || '';

  if (contentType) {
    if (contentType.startsWith('image/')) return <ImageIcon style={iconStyle} />;
    if (contentType === 'application/pdf') return <PictureAsPdfIcon style={iconStyle} />;
    if (contentType.startsWith('audio/')) return <AudiotrackIcon style={iconStyle} />;
    if (contentType.startsWith('video/')) return <VideocamIcon style={iconStyle} />;
    if (contentType === 'application/zip' || contentType === 'application/x-zip-compressed') return <FolderZipIcon style={iconStyle} />;
    if (contentType === 'text/markdown') return <ArticleIcon style={iconStyle} />;
    if (contentType === 'text/plain') return <DescriptionIcon style={iconStyle} />;
    if (contentType === 'text/csv') return <TableChartIcon style={iconStyle} />;
    if (contentType.includes('excel') || contentType.includes('spreadsheetml')) return <TableChartIcon style={iconStyle} />;
    if (contentType.startsWith('text/')) return <DescriptionIcon style={iconStyle} />; // Generic text
  }

  // Fallback to extension if contentType didn't match or wasn't provided
  switch (extension) {
    case 'jpg':
    case 'jpeg':
    case 'png':
    case 'gif':
    case 'bmp':
    case 'webp':
    case 'svg':
      return <ImageIcon style={iconStyle} />;
    case 'pdf':
      return <PictureAsPdfIcon style={iconStyle} />;
    case 'txt':
      return <DescriptionIcon style={iconStyle} />;
    case 'md':
      return <ArticleIcon style={iconStyle} />;
    case 'zip':
    case 'rar':
    case '7z':
    case 'tar':
    case 'gz':
      return <FolderZipIcon style={iconStyle} />;
    case 'mp3':
    case 'wav':
    case 'ogg':
      return <AudiotrackIcon style={iconStyle} />;
    case 'mp4':
    case 'avi':
    case 'mov':
    case 'wmv':
    case 'mkv':
      return <VideocamIcon style={iconStyle} />;
    case 'js':
    case 'jsx':
    case 'ts':
    case 'tsx':
    case 'py':
    case 'java':
    case 'cs':
    case 'cpp':
    case 'c':
    case 'html':
    case 'css':
    case 'json':
    case 'xml':
      return <CodeIcon style={iconStyle} />;
    case 'csv':
    case 'xls':
    case 'xlsx':
      return <TableChartIcon style={iconStyle} />;
    default:
      return <InsertDriveFileIcon style={iconStyle} />;
  }
};
