import { Box, Container, Paper, Stack, Typography } from "@mui/material";
import type { ReactNode } from "react";
import styles from "../styles/pageContainer.module.css";

type PageContainerProps = {
  title: string;
  description: string;
  children?: ReactNode;
};

const PageContainer = ({
  title,
  description,
  children,
}: PageContainerProps) => (
  <Container maxWidth="lg" className={styles.container}>
    <Paper className={styles.paper}>
      <Stack spacing={2} className={styles.contentStack}>
        <Box className={styles.header}>
          <Typography variant="h3" component="h1" gutterBottom>
            {title}
          </Typography>
          <Typography variant="body1" color="text.secondary">
            {description}
          </Typography>
        </Box>
        {children}
      </Stack>
    </Paper>
  </Container>
);

export default PageContainer;
