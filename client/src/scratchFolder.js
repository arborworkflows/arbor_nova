export default async (girderRest) => {
  let folder;
  let currentUser = (await girderRest.get('user/me')).data;
  if (!currentUser) {
    currentUser = (await girderRest.login('anonymous', 'letmein')).data.user;
  }
  folder = (await girderRest.get('/folder', {
    params: {parentType: 'user',
              parentId: currentUser._id,
              name: 'Private'}})).data[0];
  return folder;
}  
